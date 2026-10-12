from datetime import timedelta
from uuid import UUID, uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.test import TestCase, override_settings
from django.urls import include, path
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from src.infrastructure.api.rest.permissions import PrimerAccesoCompleto
from src.infrastructure.api.rest.views.superadmin import SuperadminView
from src.infrastructure.persistence.django.models import (
    AceptacionPolitica, AuditableModel, PoliticaSistema,
)


class FunctionalProbe(APIView):
    """Endpoint de prueba que usa los permisos globales reales de DRF."""
    def get(self, request):
        return Response({'ok': True})


urlpatterns = [path('functional-probe/', FunctionalProbe.as_view()), path('', include('config.urls'))]
BASE = '/api/auth/primer-acceso/'
TEMPORAL = 'Temporal-institucional-582!'
NUEVA = 'Mi-clave-personal-927!'
User = get_user_model()


@override_settings(
    ROOT_URLCONF=__name__,
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
)
class PrimerAccesoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='ana.prueba@saspel.com', email='ana.prueba@saspel.com',
            password=TEMPORAL, first_name='Ana', last_name='Prueba', debe_cambiar_password=True,
        )
        self.user.groups.add(Group.objects.get(name='NUEVO_TRABAJADOR'))
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(self.user)))

    def policy(self, **changes):
        data = dict(tipo='TERMINOS_USO', titulo='Documento ficticio de prueba', version='1',
                    contenido='Contenido exclusivo para pruebas automatizadas.', activo=True,
                    vigente_desde=timezone.now() - timedelta(days=1))
        return PoliticaSistema.objects.create(**(data | changes))

    def change(self, **changes):
        return self.client.post(BASE + 'password/', dict(password=NUEVA, password_confirmation=NUEVA) | changes, format='json')

    def accept(self, *policies):
        return self.client.post(BASE + 'aceptar/', {'politicas': [str(p.pk) for p in policies]}, format='json')

    def test_existing_accounts_default_to_no_password_change(self):
        existing = User.objects.create_user(username='existing@saspel.com')
        existing.refresh_from_db()
        self.assertFalse(existing.debe_cambiar_password)

    def test_creation_sets_flag_only_for_required_roles(self):
        root = User.objects.create_superuser(username='root@saspel.com', email='root@saspel.com', password=TEMPORAL)
        root.groups.add(Group.objects.get(name='SUPERADMIN'))
        self.client.force_authenticate(root)
        for index, role in enumerate(('NUEVO_TRABAJADOR', 'PSICOLOGO', 'ADMIN', 'SUPERADMIN')):
            with self.subTest(role=role):
                response = self.client.post('/api/superadmin/users/', {
                    'first_name': 'Persona', 'last_name': 'Prueba', 'apellido_materno': '',
                    'codigo_empleado': f'PRIMER-{index}', 'fecha_nacimiento': '1990-01-01',
                    'role': role, 'password': TEMPORAL, 'password_confirmation': TEMPORAL,
                }, format='json')
                self.assertEqual(response.status_code, 201, response.data)
                created = User.objects.get(pk=response.data['id'])
                self.assertEqual(created.debe_cambiar_password, role != 'SUPERADMIN')
        response = self.client.post('/api/superadmin/users/', {
            'first_name': 'Persona', 'last_name': 'Prueba', 'apellido_materno': '',
            'codigo_empleado': 'NO-WORKER', 'fecha_nacimiento': '1990-01-01',
            'role': 'TRABAJADOR', 'password': TEMPORAL, 'password_confirmation': TEMPORAL,
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_password_validation_confirmation_and_same_password_preserve_account(self):
        before = self.user.password
        for password, confirmation in [('weak', 'weak'), (NUEVA, 'different'),
                                       ('password1', 'password1'), (TEMPORAL, TEMPORAL)]:
            with self.subTest(password_length=len(password)):
                response = self.change(password=password, password_confirmation=confirmation)
                self.assertEqual(response.status_code, 400, response.data)
                self.user.refresh_from_db()
                self.assertTrue(self.user.debe_cambiar_password)
                self.assertEqual(self.user.password, before)

    def test_password_is_hashed_flag_cleared_and_old_password_stops_working(self):
        policy = self.policy()
        response = self.change()
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['siguiente_ruta'], '/primer-acceso/politicas')
        self.assertEqual(response.data['politicas_pendientes'], (policy.pk,))
        self.user.refresh_from_db()
        self.assertFalse(self.user.debe_cambiar_password)
        self.assertTrue(self.user.check_password(NUEVA))
        self.assertFalse(self.user.check_password(TEMPORAL))
        self.assertNotIn(NUEVA, repr(response.data))
        self.assertEqual(self.user.actualizado_por, str(self.user.pk))
        self.assertEqual(self.change().status_code, 400)
        for password, expected in ((TEMPORAL, 401), (NUEVA, 200)):
            login = APIClient().post('/api/auth/login/', {'email': self.user.email, 'password': password}, format='json')
            self.assertEqual(login.status_code, expected)

    def test_only_active_effective_mandatory_policies_are_pending(self):
        active = self.policy()
        self.policy(tipo='PRIVACIDAD_DATOS', activo=False)
        self.policy(tipo='CONSENTIMIENTO_EVALUACION', vigente_desde=timezone.now() + timedelta(days=2))
        self.policy(version='optional', activo=False, obligatoria=False)
        response = self.client.get(BASE + 'politicas/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p['id'] for p in response.data], [active.pk])
        self.assertEqual(response.data[0]['contenido'], active.contenido)
        self.assertFalse(AceptacionPolitica.objects.exists())
        active.obligatoria = False
        with self.assertRaises(ValidationError):
            active.save()

    def test_optional_active_and_deleted_policies_do_not_block(self):
        self.policy(obligatoria=False)
        self.policy(tipo='PRIVACIDAD_DATOS', activo=False, deleted=True)
        self.change()
        self.assertTrue(self.client.get(BASE).data['completo'])

    def test_cannot_accept_before_password_or_on_behalf_of_another_account(self):
        policy = self.policy()
        self.assertEqual(self.accept(policy).status_code, 400)
        self.change()
        response = self.client.post(BASE + 'aceptar/', {
            'politicas': [str(policy.pk)], 'usuario_id': str(uuid4()),
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AceptacionPolitica.objects.exists())

    def test_acceptance_is_explicit_idempotent_and_completes_access(self):
        policies = [self.policy(), self.policy(tipo='PRIVACIDAD_DATOS')]
        self.change()
        self.assertEqual(self.accept().status_code, 400)
        first = self.accept(policies[0])
        self.assertFalse(first.data['completo'])
        self.assertEqual(first.data['politicas_pendientes'], (policies[1].pk,))
        row = AceptacionPolitica.objects.get()
        timestamp = row.fecha_aceptacion
        response = self.accept(*policies)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['completo'])
        self.assertEqual(response.data['siguiente_ruta'], '/dashboard/nuevo-trabajador')
        self.assertEqual(self.accept(*policies).status_code, 200)
        self.assertEqual(AceptacionPolitica.objects.count(), 2)
        row.refresh_from_db()
        self.assertEqual(row.fecha_aceptacion, timestamp)
        self.assertEqual(row.creado_por, str(self.user.pk))

    def test_new_version_blocks_again_and_preserves_acceptance_after_role_change(self):
        original_id = self.user.pk
        old = self.policy()
        self.change()
        self.accept(old)
        acceptance = AceptacionPolitica.objects.get()
        # Simula una futura transición; no incorpora un endpoint de promoción.
        self.user.groups.set([Group.objects.get(name='TRABAJADOR')])
        self.assertTrue(self.client.get(BASE).data['completo'])
        old.activo = False
        old.save(update_fields=['activo'])
        new = self.policy(version='2')
        state = self.client.get(BASE).data
        self.assertEqual(state['politicas_pendientes'], (new.pk,))
        self.assertEqual(self.client.get('/functional-probe/').status_code, 403)
        self.assertEqual(self.accept(new).data['siguiente_ruta'], '/dashboard/trabajador')
        acceptance.refresh_from_db()
        self.assertEqual(acceptance.usuario_id, original_id)
        self.assertEqual(acceptance.politica_id, old.pk)
        self.assertEqual(AceptacionPolitica.objects.count(), 2)
        self.assertEqual(self.client.get('/functional-probe/').status_code, 200)

    def test_stale_inactive_future_and_unknown_versions_cannot_be_accepted(self):
        old = self.policy()
        self.change()
        old.activo = False
        old.save(update_fields=['activo'])
        new = self.policy(version='2', vigente_desde=timezone.now() + timedelta(days=1))
        for policy_id in (old.pk, new.pk, uuid4()):
            response = self.client.post(BASE + 'aceptar/', {'politicas': [str(policy_id)]}, format='json')
            self.assertEqual(response.status_code, 400)
        self.assertFalse(AceptacionPolitica.objects.exists())

    def test_functional_gate_and_auth_allowlist_with_current_jwt(self):
        policy = self.policy()
        response = self.client.get('/functional-probe/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['code'], 'primer_acceso_pendiente')
        self.assertEqual(response.data['siguiente_ruta'], '/primer-acceso/password')
        for url in ('/api/auth/me/', BASE, BASE + 'politicas/'):
            self.assertEqual(self.client.get(url).status_code, 200)
        login = APIClient().post('/api/auth/login/', {'email': self.user.email, 'password': TEMPORAL}, format='json')
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.data['user']['primer_acceso']['siguiente_ruta'], '/primer-acceso/password')
        refresh = APIClient().post('/api/auth/refresh/', {'refresh': str(RefreshToken.for_user(self.user))}, format='json')
        self.assertEqual(refresh.status_code, 200)
        self.change()
        self.assertEqual(self.client.get('/functional-probe/').data['siguiente_ruta'], '/primer-acceso/politicas')
        self.accept(policy)
        self.assertEqual(self.client.get('/functional-probe/').status_code, 200)
        self.assertIn(PrimerAccesoCompleto, SuperadminView.permission_classes)
        # Completar onboarding no eleva permisos funcionales.
        self.assertEqual(self.client.get('/api/superadmin/users/').status_code, 403)

    def test_superadmin_excluded_even_with_pending_flag_and_policy(self):
        self.user.groups.set([Group.objects.get(name='SUPERADMIN')])
        self.policy()
        state = self.client.get(BASE).data
        self.assertTrue(state['completo'])
        self.assertFalse(state['debe_cambiar_password'])
        self.assertEqual(state['siguiente_ruta'], '/dashboard/superadmin')
        self.assertEqual(self.client.get(BASE + 'politicas/').data, [])
        self.assertEqual(self.client.get('/api/superadmin/users/').status_code, 200)

    def test_endpoints_require_authentication(self):
        anonymous = APIClient()
        for method, url, data in (
            ('get', BASE, {}), ('get', BASE + 'politicas/', {}),
            ('post', BASE + 'password/', {'password': NUEVA, 'password_confirmation': NUEVA}),
            ('post', BASE + 'aceptar/', {'politicas': [str(uuid4())]}),
            ('get', '/functional-probe/', {}),
        ):
            with self.subTest(url=url):
                self.assertEqual(getattr(anonymous, method)(url, data, format='json').status_code, 401)

    def test_unique_policy_version_active_type_and_acceptance_enforced_in_database(self):
        policy = self.policy()
        for changes in ({'version': '2'}, {'activo': False}):
            duplicate = PoliticaSistema(tipo=policy.tipo, titulo='Prueba', version='1', contenido='Prueba', activo=True)
            for name, value in changes.items():
                setattr(duplicate, name, value)
            with self.assertRaises(IntegrityError), transaction.atomic():
                PoliticaSistema.objects.bulk_create([duplicate])
        AceptacionPolitica.objects.create(usuario=self.user, politica=policy)
        with self.assertRaises(IntegrityError), transaction.atomic():
            AceptacionPolitica.objects.create(usuario=self.user, politica=policy)

    def test_history_cannot_be_deleted_or_accepted_content_rewritten(self):
        policy = self.policy()
        self.change()
        self.accept(policy)
        policy.activo = False
        policy.save(update_fields=['activo'])
        policy.contenido = 'Cambio no permitido'
        with self.assertRaises(ValidationError):
            policy.save()
        for target in (policy, PoliticaSistema.objects.all(), AceptacionPolitica.objects.get(), AceptacionPolitica.objects.all()):
            with self.assertRaises(ValidationError):
                target.delete()

    def test_new_entities_have_uuid_and_existing_audit_columns(self):
        policy = self.policy()
        self.change()
        self.accept(policy)
        for row in (policy, AceptacionPolitica.objects.get()):
            self.assertIsInstance(row, AuditableModel)
            self.assertIsInstance(row.pk, UUID)
            self.assertEqual(row.pk.version, 4)
            self.assertFalse(row.deleted)
            self.assertIsNotNone(row.creado_en)
            self.assertIsNotNone(row.actualizado_en)
            with connection.cursor() as cursor:
                columns = {c.name for c in connection.introspection.get_table_description(cursor, row._meta.db_table)}
            self.assertTrue({'id', 'Time_Create', 'Time_Update', 'User_Create', 'User_Update', 'deleted'} <= columns)
