"""T23 con JWT real y PostgreSQL temporal: permisos, elegibilidad, historial y rollback."""

from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from src.infrastructure.persistence.django.models import AsignacionProfesional, PerfilUsuario

User = get_user_model()
BASE = '/api/superadmin/assignments/'


def person(name, role, active=True, enabled=True, profile=True):
    """Cuenta ficticia sin contraseña utilizable; solo vive en la base temporal de tests."""
    user = User.objects.create_user(username=name, email=f'{name}@example.com', first_name=name, is_active=active)
    user.groups.add(Group.objects.get_or_create(name=role)[0])
    if profile:
        PerfilUsuario.objects.create(usuario=user, codigo_empleado=name, habilitado_asignaciones=enabled)
    return user


class AssignmentApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = person('t23-root', 'SUPERADMIN')
        cls.worker = person('t23-worker', 'TRABAJADOR')
        cls.new_worker = person('t23-new', 'NUEVO_TRABAJADOR')
        cls.psychologist = person('t23-psychologist', 'PSICOLOGO')
        cls.other_psychologist = person('t23-other-psychologist', 'PSICOLOGO')

    def setUp(self):
        self.client = APIClient()
        self.authorize(self.admin)

    def authorize(self, user):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(user)))

    def assign(self, worker=None, psychologist=None, **extra):
        return self.client.post(BASE, {
            'trabajador_id': (worker or self.worker).pk,
            'psicologo_id': (psychologist or self.psychologist).pk, **extra,
        }, format='json')

    def action(self, assignment_id, action, **data):
        return self.client.post(f'{BASE}{assignment_id}/{action}/', data, format='json')

    def test_valid_assignment_and_no_role_or_screening_changes(self):
        response = self.assign()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estado'], 'ACTIVA')
        self.assertIsNone(response.data['fecha_fin'])
        self.assertEqual(response.data['trabajador']['id'], self.worker.pk)
        self.assertEqual(response.data['psicologo']['id'], self.psychologist.pk)
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.worker.perfil_usuario.refresh_from_db()
        self.assertFalse(self.worker.perfil_usuario.tamizaje_resuelto)
        self.assertEqual(list(self.worker.groups.values_list('name', flat=True)), ['TRABAJADOR'])

    def test_manual_assignment_also_accepts_new_worker_without_promoting_role(self):
        self.assertEqual(self.assign(worker=self.new_worker).status_code, 201)
        self.assertEqual(list(self.new_worker.groups.values_list('name', flat=True)), ['NUEVO_TRABAJADOR'])
        self.new_worker.perfil_usuario.refresh_from_db()
        self.assertFalse(self.new_worker.perfil_usuario.tamizaje_resuelto)

    def test_second_active_assignment_rejected(self):
        self.assign()
        response = self.assign(psychologist=self.other_psychologist)
        self.assertEqual(response.status_code, 400)
        self.assertIn('trabajador_id', response.data)
        self.assertEqual(AsignacionProfesional.objects.count(), 1)

    def test_ineligible_psychologists_rejected(self):
        for name, role, active, enabled, profile in [
            ('disabled', 'PSICOLOGO', True, False, True),
            ('inactive', 'PSICOLOGO', False, True, True),
            ('not-psych', 'ADMIN', True, True, True),
            ('no-profile', 'PSICOLOGO', True, True, False),
        ]:
            with self.subTest(name=name):
                response = self.assign(psychologist=person(name, role, active, enabled, profile))
                self.assertEqual(response.status_code, 400)
                self.assertIn('psicologo_id', response.data)
        self.assertEqual(AsignacionProfesional.objects.count(), 0)

    def test_functional_role_priority_is_respected(self):
        self.psychologist.groups.add(Group.objects.get(name='SUPERADMIN'))
        self.assertEqual(self.assign().status_code, 400)
        ids = [row['psicologo']['id'] for row in self.client.get(BASE + 'psychologists/').data]
        self.assertNotIn(self.psychologist.pk, ids)

    def test_invalid_worker_and_self_assignment_rejected(self):
        inactive = person('inactive-worker', 'TRABAJADOR', active=False)
        for worker in [self.psychologist, self.admin, inactive]:
            with self.subTest(worker=worker.pk):
                self.assertEqual(self.assign(worker=worker).status_code, 400)
        self.assertFalse(AsignacionProfesional.objects.exists())

    def test_missing_person_or_assignment_is_404(self):
        response = self.client.post(BASE, {'trabajador_id': 999999, 'psicologo_id': self.psychologist.pk}, format='json')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.action(999999, 'finish', motivo_fin='Fin').status_code, 404)
        self.assertEqual(self.action(999999, 'reassign', motivo_fin='Cambio', psicologo_id=self.psychologist.pk).status_code, 404)

    def test_reassignment_preserves_history_and_load(self):
        old_id = self.assign().data['id']
        response = self.action(old_id, 'reassign', psicologo_id=self.other_psychologist.pk, motivo_fin=' Cambio de disponibilidad ')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertNotEqual(response.data['id'], old_id)
        old = AsignacionProfesional.objects.get(pk=old_id)
        self.assertEqual(old.estado, 'REASIGNADA')
        self.assertEqual(old.motivo_fin, 'Cambio de disponibilidad')
        self.assertIsNotNone(old.fecha_fin)
        self.assertEqual(old.psicologo_id, self.psychologist.pk)
        self.assertEqual(AsignacionProfesional.objects.filter(estado='ACTIVA').count(), 1)
        history = self.client.get(BASE, {'trabajador_id': self.worker.pk}).data
        self.assertEqual(history['count'], 2)
        self.assertEqual([item['estado'] for item in history['results']], ['ACTIVA', 'REASIGNADA'])
        loads = {row['psicologo']['id']: row['trabajadores_activos'] for row in self.client.get(BASE + 'psychologists/').data}
        self.assertEqual(loads, {self.psychologist.pk: 0, self.other_psychologist.pk: 1})

    def test_finish_releases_worker_and_allows_new_assignment(self):
        old_id = self.assign().data['id']
        self.assertNotIn(self.worker.pk, [row['id'] for row in self.client.get(BASE + 'unassigned-workers/').data['results']])
        response = self.action(old_id, 'finish', motivo_fin='Finalización manual')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['estado'], 'FINALIZADA')
        self.assertIsNotNone(response.data['fecha_fin'])
        workers = self.client.get(BASE + 'unassigned-workers/').data['results']
        self.assertIn(self.worker.pk, [row['id'] for row in workers])
        self.assertEqual(self.assign().status_code, 201)
        self.assertEqual(AsignacionProfesional.objects.count(), 2)

    def test_stale_actions_do_not_close_the_new_assignment(self):
        old_id = self.assign().data['id']
        new = self.action(old_id, 'reassign', psicologo_id=self.other_psychologist.pk, motivo_fin='Cambio').data
        self.assertEqual(self.action(old_id, 'finish', motivo_fin='Otra petición').status_code, 400)
        self.assertEqual(self.action(old_id, 'reassign', psicologo_id=self.psychologist.pk, motivo_fin='Reintento').status_code, 400)
        self.assertEqual(AsignacionProfesional.objects.get(pk=new['id']).estado, 'ACTIVA')

    def test_finish_is_allowed_after_worker_or_psychologist_deactivation(self):
        assignment_id = self.assign().data['id']
        User.objects.filter(pk__in=[self.worker.pk, self.psychologist.pk]).update(is_active=False)
        self.assertEqual(self.action(assignment_id, 'finish', motivo_fin='Baja').status_code, 200)

    def test_reassignment_to_same_or_disabled_psychologist_preserves_previous(self):
        assignment_id = self.assign().data['id']
        PerfilUsuario.objects.filter(usuario=self.other_psychologist).update(habilitado_asignaciones=False)
        for target in [self.psychologist, self.other_psychologist]:
            response = self.action(assignment_id, 'reassign', psicologo_id=target.pk, motivo_fin='Cambio')
            self.assertEqual(response.status_code, 400)
        previous = AsignacionProfesional.objects.get(pk=assignment_id)
        self.assertEqual(previous.estado, 'ACTIVA')
        self.assertIsNone(previous.fecha_fin)
        self.assertEqual(AsignacionProfesional.objects.count(), 1)

    def test_failure_creating_replacement_rolls_back_the_close(self):
        assignment_id = self.assign().data['id']
        with patch('src.infrastructure.persistence.django.repositories.assignments.DjangoAssignmentRepository.create_assignment', side_effect=IntegrityError):
            response = self.action(assignment_id, 'reassign', psicologo_id=self.other_psychologist.pk, motivo_fin='Cambio')
        self.assertEqual(response.status_code, 400)
        previous = AsignacionProfesional.objects.get(pk=assignment_id)
        self.assertEqual((previous.estado, previous.fecha_fin, previous.motivo_fin), ('ACTIVA', None, ''))
        self.assertEqual(AsignacionProfesional.objects.count(), 1)

    def test_filters_search_pagination_and_no_delete_endpoint(self):
        assignment_id = self.assign().data['id']
        self.assertEqual(self.client.get(BASE, {'estado': 'FINALIZADA'}).data['count'], 0)
        self.assertEqual(self.client.get(BASE, {'estado': 'ACTIVA', 'psicologo_id': self.psychologist.pk, 'search': 't23-worker'}).data['count'], 1)
        self.assertEqual(self.client.get(BASE, {'page': 2}).data['results'], [])
        self.assertEqual(self.client.get(BASE, {'estado': 'BORRADA'}).status_code, 400)
        self.assertEqual(self.client.get(BASE, {'page': 0}).status_code, 400)
        self.assertEqual(self.client.delete(BASE).status_code, 405)
        self.assertEqual(self.client.delete(f'{BASE}{assignment_id}/finish/').status_code, 405)
        self.assertEqual(AsignacionProfesional.objects.count(), 1)

    def test_unassigned_workers_excludes_other_roles_inactive_and_active_links(self):
        self.assign()
        person('inactive-new', 'NUEVO_TRABAJADOR', active=False)
        response = self.client.get(BASE + 'unassigned-workers/').data
        self.assertEqual([row['id'] for row in response['results']], [self.new_worker.pk])
        self.assertEqual(self.client.get(BASE + 'unassigned-workers/', {'search': 'not-found'}).data['count'], 0)
        self.assertEqual(self.client.get(BASE + 'unassigned-workers/', {'page': 2}).data['results'], [])

    def test_psychologist_list_requires_active_and_enabled_and_includes_zero_load(self):
        person('not-enabled-list', 'PSICOLOGO', enabled=False)
        person('not-active-list', 'PSICOLOGO', active=False)
        response = self.client.get(BASE + 'psychologists/').data
        self.assertEqual({row['psicologo']['id'] for row in response}, {self.psychologist.pk, self.other_psychologist.pk})
        self.assertTrue(all(row['trabajadores_activos'] == 0 for row in response))

    def test_reason_and_strict_payload_validation(self):
        self.assertEqual(self.assign(estado='FINALIZADA').status_code, 400)
        assignment_id = self.assign().data['id']
        for reason in ['', '  ', 'x' * 2001]:
            with self.subTest(length=len(reason)):
                self.assertEqual(self.action(assignment_id, 'finish', motivo_fin=reason).status_code, 400)
        self.assertEqual(self.action(assignment_id, 'finish', motivo_fin='Fin', estado='REASIGNADA').status_code, 400)
        self.assertEqual(AsignacionProfesional.objects.get(pk=assignment_id).estado, 'ACTIVA')

    def test_all_endpoints_require_jwt_and_superadmin_group(self):
        endpoints = [
            ('get', BASE, {}), ('post', BASE, {}),
            ('get', BASE + 'unassigned-workers/', {}), ('get', BASE + 'psychologists/', {}),
            ('post', BASE + '1/finish/', {}), ('post', BASE + '1/reassign/', {}),
        ]
        self.client.credentials()
        for method, path, data in endpoints:
            self.assertEqual(getattr(self.client, method)(path, data, format='json').status_code, 401)
        for role in ['ADMIN', 'PSICOLOGO', 'TRABAJADOR', 'NUEVO_TRABAJADOR']:
            self.authorize(person('denied-' + role, role))
            for method, path, data in endpoints:
                with self.subTest(role=role, path=path):
                    self.assertEqual(getattr(self.client, method)(path, data, format='json').status_code, 403)
        technical = User.objects.create_user(username='technical-only', is_superuser=True)
        self.authorize(technical)
        self.assertEqual(self.client.get(BASE).status_code, 403)

    def test_old_token_loses_permission_after_removing_group(self):
        self.admin.groups.clear()
        self.assertEqual(self.client.get(BASE).status_code, 403)
