from uuid import UUID, uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from src.infrastructure.persistence.django.models import AreaCargo, AreaInstitucional, CargoInstitucional, PerfilUsuario


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AreaCargoApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = get_user_model().objects.create_superuser(username='root@saspel.com', password='Root-8274!')
        cls.root.groups.add(Group.objects.get(name='SUPERADMIN'))
        cls.area = AreaInstitucional.objects.create(nombre='Área de TIC')
        cls.other = AreaInstitucional.objects.create(nombre='Área de Negocios')
        cls.cargo = CargoInstitucional.objects.create(nombre='Z SISTEMAS')
        cls.shared = CargoInstitucional.objects.create(nombre='A COMPARTIDO')
        cls.foreign = CargoInstitucional.objects.create(nombre='NEGOCIOS')
        cls.relation = AreaCargo.objects.create(area=cls.area, cargo=cls.cargo)
        AreaCargo.objects.create(area=cls.area, cargo=cls.shared)
        AreaCargo.objects.create(area=cls.other, cargo=cls.shared)
        AreaCargo.objects.create(area=cls.other, cargo=cls.foreign)

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(self.root)))

    def create(self, **changes):
        return self.client.post('/api/superadmin/users/', {
            'first_name': 'Ana', 'last_name': 'Prueba', 'apellido_materno': '',
            'codigo_empleado': 'AREA-1', 'fecha_nacimiento': '1990-01-01',
            'password': 'Personal-segura-8274!', 'password_confirmation': 'Personal-segura-8274!',
            'role': 'NUEVO_TRABAJADOR', 'area_id': str(self.area.pk), 'cargo_id': str(self.cargo.pk),
        } | changes, format='json')

    def cargos(self, area=None, **params):
        return self.client.get('/api/superadmin/cargos/', {'area': str(area or self.area.pk)} | params)

    def test_filter_returns_only_related_cargos_in_alphabetical_order_and_uuid_strings(self):
        result = self.cargos()
        self.assertEqual(result.status_code, 200)
        self.assertEqual([c['nombre'] for c in result.json()], ['A COMPARTIDO', 'Z SISTEMAS'])
        self.assertEqual([c['id'] for c in result.json()], [str(self.shared.pk), str(self.cargo.pk)])
        self.assertEqual([c['nombre'] for c in self.cargos(self.other.pk).data], ['A COMPARTIDO', 'NEGOCIOS'])
        self.assertEqual(len(self.client.get('/api/superadmin/cargos/').data), 3)
        self.assertEqual(self.cargos(uuid4()).data, [])
        self.assertEqual(self.cargos('not-a-uuid').status_code, 400)

    def test_filter_excludes_deleted_relations_and_inactive_or_deleted_catalogs(self):
        for row, field in ((self.relation, 'deleted'), (self.cargo, 'deleted'), (self.cargo, 'activo'),
                           (self.area, 'deleted'), (self.area, 'activo')):
            with self.subTest(model=type(row).__name__, field=field), transaction.atomic():
                type(row).objects.filter(pk=row.pk).update(**{field: field == 'deleted'})
                result = self.cargos()
                self.assertNotIn(str(self.cargo.pk), [c['id'] for c in result.json()])
                if row == self.area:
                    self.assertEqual(result.data, [])
                transaction.set_rollback(True)

    def test_valid_create_preserves_roles_uuid_first_access_and_superadmin(self):
        before = get_user_model().objects.values().get(pk=self.root.pk)
        result = self.create()
        self.assertEqual(result.status_code, 201, result.data)
        user = get_user_model().objects.get(pk=result.data['id'])
        self.assertIsInstance(user.pk, UUID)
        self.assertTrue(user.debe_cambiar_password)
        self.assertEqual(list(user.groups.values_list('name', flat=True)), ['NUEVO_TRABAJADOR'])
        self.assertEqual(user.perfil_usuario.area_id, self.area.pk)
        self.assertEqual(user.perfil_usuario.cargo_id, self.cargo.pk)
        self.assertEqual(get_user_model().objects.values().get(pk=self.root.pk), before)
        self.assertEqual(self.create(codigo_empleado='AREA-2', role='TRABAJADOR').status_code, 400)

    def test_cargo_without_area_and_foreign_cargo_rejected_without_partial_user(self):
        for changes in ({'area_id': None}, {'cargo_id': str(self.foreign.pk)}):
            result = self.create(**changes)
            self.assertEqual(result.status_code, 400)
            self.assertIn('cargo_id', result.data)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(PerfilUsuario.objects.count(), 0)

    def test_inactive_deleted_and_missing_relations_reject_user_creation(self):
        for row, field in ((self.relation, 'deleted'), (self.cargo, 'deleted'), (self.cargo, 'activo'),
                           (self.area, 'deleted'), (self.area, 'activo')):
            with self.subTest(model=type(row).__name__, field=field), transaction.atomic():
                type(row).objects.filter(pk=row.pk).update(**{field: field == 'deleted'})
                self.assertEqual(self.create().status_code, 400)
                transaction.set_rollback(True)
        self.relation.delete()
        self.assertEqual(self.create().status_code, 400)

    def test_patch_checks_resulting_pair_and_valid_changes_preserve_identity(self):
        created = self.create().data
        url = f'/api/superadmin/users/{created["id"]}/'
        before = get_user_model().objects.get(pk=created['id'])
        for changes in ({'area_id': None}, {'area_id': str(self.other.pk)}, {'cargo_id': str(self.foreign.pk)}):
            response = self.client.patch(url, changes, format='json')
            self.assertEqual(response.status_code, 400, response.data)
            self.assertEqual(PerfilUsuario.objects.get(usuario=before).cargo_id, self.cargo.pk)
        result = self.client.patch(url, {'area_id': str(self.other.pk), 'cargo_id': str(self.foreign.pk)}, format='json')
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data['area']['id'], self.other.pk)
        self.assertEqual(result.data['cargo']['id'], self.foreign.pk)
        user = get_user_model().objects.get(pk=before.pk)
        self.assertEqual(user.email, before.email)
        self.assertEqual(user.password, before.password)
        self.assertEqual(self.client.patch(url, {'cargo_id': str(self.shared.pk)}, format='json').status_code, 200)
        self.assertEqual(self.client.patch(url, {'area_id': str(self.area.pk)}, format='json').status_code, 200)
        self.assertEqual(self.client.patch(url, {'area_id': None, 'cargo_id': None}, format='json').status_code, 200)

    def test_unrelated_edits_preserve_historical_links_but_explicit_invalid_pair_is_rejected(self):
        created = self.create().data
        url = f'/api/superadmin/users/{created["id"]}/'
        AreaCargo.objects.filter(pk=self.relation.pk).update(deleted=True)
        result = self.client.patch(url, {'telefono': '70000000'}, format='json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['cargo']['id'], self.cargo.pk)
        result = self.client.patch(url, {'cargo_id': str(self.cargo.pk)}, format='json')
        self.assertEqual(result.status_code, 400)

    def test_pair_is_unique_but_cargo_can_belong_to_several_areas(self):
        self.assertEqual(AreaCargo.objects.filter(cargo=self.shared).count(), 2)
        with self.assertRaises(IntegrityError), transaction.atomic():
            AreaCargo.objects.create(area=self.area, cargo=self.cargo)
        self.relation.deleted = True
        self.relation.save(update_fields=['deleted'])
        with self.assertRaises(IntegrityError), transaction.atomic():
            AreaCargo.objects.create(area=self.area, cargo=self.cargo)
