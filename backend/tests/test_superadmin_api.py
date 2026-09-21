"""Comprueba administración real por HTTP/JWT sobre PostgreSQL temporal: registro, filtros,
permisos, estados, roles, claves y catálogos. Usa hash rápido solo en pruebas; conservar los
escenarios de rollback y de acceso con token anterior al cambiar el módulo.
"""

from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import caches
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from src.application.use_cases.superadmin import ChangeUserRole, DeactivateUser
from src.domain.exceptions.superadmin import AdministrationError
from src.infrastructure.dependencies.superadmin import build_administration
from src.infrastructure.persistence.django.models import AreaInstitucional, CargoInstitucional, PerfilUsuario

User = get_user_model()
PASSWORD = 'Prueba-segura-8274!'


@override_settings(
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    CACHES={
        'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
        'login_attempts': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'saspel-superadmin-tests'},
    },
)
class SuperadminApiTests(TestCase):
    """Escenarios integrados de SA-01 con cuenta administrativa y catálogos ficticios."""
    @classmethod
    def setUpTestData(cls):
        cls.root = User.objects.create_user(username='root@example.com', email='root@example.com', password=PASSWORD, is_superuser=True)
        cls.root.groups.add(Group.objects.get(name='SUPERADMIN'))
        cls.area = AreaInstitucional.objects.create(nombre='Área de pruebas')
        cls.cargo = CargoInstitucional.objects.create(nombre='Cargo de pruebas')

    def setUp(self):
        caches['login_attempts'].clear()
        self.addCleanup(caches['login_attempts'].clear)
        self.client = APIClient()
        self.authorize(self.root)

    def authorize(self, user):
        """Instala en APIClient un access JWT de la cuenta indicada para probar permisos reales."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(user)))

    def payload(self, **changes):
        """Devuelve un alta ficticia válida con sobrescrituras para provocar cada escenario; no
        crea datos.
        """
        data = dict(password=PASSWORD, password_confirmation=PASSWORD,
                    first_name='Ana', last_name='Prueba', apellido_materno='López', codigo_empleado='SA-001',
                    role='NUEVO_TRABAJADOR', area_id=self.area.pk, cargo_id=self.cargo.pk)
        return data | changes

    def create(self, **changes):
        """Envía el alta ficticia con cambios al endpoint y devuelve su respuesta HTTP."""
        return self.client.post('/api/superadmin/users/', self.payload(**changes), format='json')

    def action(self, user_id, action, data=None):
        """Envía POST a una acción de persona con ID y datos opcionales; devuelve la respuesta."""
        return self.client.post(f'/api/superadmin/users/{user_id}/{action}/', data or {}, format='json')

    def login(self, email='ana.prueba@saspel.com', password=PASSWORD):
        """Usa un cliente sin token administrativo para comprobar que las credenciales de la
        persona permiten entrar.
        """
        return APIClient().post('/api/auth/login/', dict(email=email, password=password), format='json')

    def test_create_each_allowed_role_and_login(self):
        """Crea cada rol permitido y comprueba perfil, hash, grupo único, login y panel
        correspondiente.
        """
        paths = {'NUEVO_TRABAJADOR': 'nuevo-trabajador', 'PSICOLOGO': 'psicologo', 'ADMIN': 'admin', 'SUPERADMIN': 'superadmin'}
        for index, (role, path) in enumerate(paths.items()):
            with self.subTest(role=role):
                email = 'ana.prueba' + (str(index + 1) if index else '') + '@saspel.com'
                response = self.create(role=role, codigo_empleado=f'EMP-{index}')
                self.assertEqual(response.status_code, 201, response.data)
                user = User.objects.get(pk=response.data['id'])
                self.assertEqual(user.email, email)
                self.assertEqual(user.username, email)
                self.assertEqual(list(user.groups.values_list('name', flat=True)), [role])
                self.assertTrue(user.check_password(PASSWORD))
                self.assertNotEqual(user.password, PASSWORD)
                self.assertNotIn('password', response.data)
                self.assertNotIn('password', repr(response.data))
                self.assertEqual(user.is_staff, role == 'SUPERADMIN')
                self.assertEqual(user.is_superuser, role == 'SUPERADMIN')
                self.assertFalse(user.perfil_usuario.tamizaje_resuelto)
                self.assertEqual(user.perfil_usuario.habilitado_asignaciones, role == 'PSICOLOGO')
                login = self.login(email)
                self.assertEqual(login.status_code, 200)
                self.assertEqual(login.data['user']['role'], role)
                self.assertEqual(login.data['dashboard_path'], '/dashboard/' + path)
                user.refresh_from_db()
                self.assertIsNotNone(user.last_login)

    def test_superadmin_lists_including_missing_profile(self):
        """Lista la cuenta inicial sin perfil para proteger el tratamiento de cuentas históricas
        incompletas.
        """
        response = self.client.get('/api/superadmin/users/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertFalse(response.data['results'][0]['tiene_perfil'])
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_all_endpoints_require_superadmin(self):
        """Intenta URLs administrativas con otros roles, is_superuser sin grupo y sin token;
        ninguno obtiene acceso.
        """
        user = User.objects.create_user(username='other', email='other@example.com', password=PASSWORD)
        endpoints = ['/dashboard/summary/', '/users/', f'/users/{self.root.pk}/', '/areas/', '/cargos/']
        for role in ('TRABAJADOR', 'ADMIN', 'PSICOLOGO', 'NUEVO_TRABAJADOR'):
            user.groups.set([Group.objects.get(name=role)])
            self.authorize(user)
            for endpoint in endpoints:
                self.assertEqual(self.client.get('/api/superadmin' + endpoint).status_code, 403)
            for action in ('activate', 'deactivate', 'role', 'reset-password'):
                self.assertEqual(self.action(self.root.pk, action).status_code, 403)
        user.is_superuser = True
        user.save()
        self.assertEqual(self.client.get('/api/superadmin/users/').status_code, 403)
        self.client.credentials()
        self.assertEqual(self.client.get('/api/superadmin/users/').status_code, 401)

    def test_inactive_and_stale_role_tokens_rejected(self):
        """Reutiliza el JWT tras desactivar la cuenta o quitar su grupo para comprobar que no
        conserva acceso.
        """
        self.root.is_active = False
        self.root.save()
        self.assertEqual(self.client.get('/api/superadmin/users/').status_code, 401)
        self.root.is_active = True
        self.root.save()
        self.root.groups.clear()
        self.assertEqual(self.client.get('/api/superadmin/users/').status_code, 403)

    def test_worker_creation_rejected(self):
        """Intenta crear TRABAJADOR directamente y comprueba rechazo sin una cuenta adicional."""
        self.assertEqual(self.create(role='TRABAJADOR').status_code, 400)
        self.assertEqual(User.objects.count(), 1)

    def test_generated_email_accents_and_special_characters(self):
        response = self.create(first_name='  Jesús Gabriel  ', last_name='Crúz Lavadenz')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['email'], 'jesus.cruz@saspel.com')
        response = self.create(first_name="Ána-María", last_name="O'Ñéill", codigo_empleado='OTHER')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['email'], 'anamaria.oneill@saspel.com')

    def test_duplicate_emails_get_numbered_including_inactive_accounts(self):
        first = self.create()
        self.assertEqual(first.status_code, 201)
        self.action(first.data['id'], 'deactivate')
        for number in (2, 3):
            response = self.create(codigo_empleado=f'OTHER-{number}')
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(response.data['email'], f'ana.prueba{number}@saspel.com')
        self.assertEqual(self.create().status_code, 400)  # Código duplicado revierte el alta.
        self.assertEqual(User.objects.count(), 4)

    def test_collision_checks_email_and_username_case_insensitively(self):
        User.objects.create_user(username='ANA.PRUEBA@SASPEL.COM', email='legacy@example.com')
        User.objects.create_user(username='legacy', email='ANA.PRUEBA2@SASPEL.COM')
        response = self.create()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['email'], 'ana.prueba3@saspel.com')

    def test_manual_email_and_invalid_name_rejected(self):
        for fields in ({'email': 'manual@example.com'}, {'username': 'manual'},
                       {'first_name': '!!!'}, {'last_name': '   '}):
            self.assertEqual(self.create(**fields).status_code, 400, fields)
        self.assertEqual(User.objects.count(), 1)

    def test_long_names_produce_valid_email(self):
        response = self.create(first_name='a' * 150, last_name='b' * 150)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertLessEqual(len(response.data['email'].split('@')[0]), 64)

    def test_existing_external_email_login_is_rejected(self):
        response = self.login('root@example.com')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {'detail': 'Credenciales no válidas.'})

    def test_administrators_category_includes_admin_and_superadmin(self):
        self.create(role='ADMIN')
        self.create(role='PSICOLOGO', codigo_empleado='PSI')
        response = self.client.get('/api/superadmin/users/', {'role': 'ADMINISTRADORES'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertCountEqual([u['role'] for u in response.data['results']], ['ADMIN', 'SUPERADMIN'])

    def test_password_validators_and_confirmation(self):
        """Prueba claves débiles y confirmación distinta para impedir altas que no cumplen las
        validaciones.
        """
        for password in ('abc1', 'onlyletters', '123456789', 'password1'):
            self.assertEqual(self.create(password=password, password_confirmation=password).status_code, 400)
        self.assertEqual(self.create(password_confirmation='different').status_code, 400)
        self.assertEqual(User.objects.count(), 1)

    def test_profile_failure_rolls_back_user(self):
        """Simula fallo al guardar perfil y comprueba que la cuenta ya creada también se
        revierta.
        """
        with patch.object(PerfilUsuario, 'save', side_effect=RuntimeError('Fallo simulado')):
            with self.assertRaises(RuntimeError):
                self.create()
        self.assertEqual(User.objects.count(), 1)

    def test_missing_group_rolls_back_user_and_profile(self):
        """Retira el grupo destino antes del alta para comprobar rollback de cuenta y perfil."""
        Group.objects.get(name='PSICOLOGO').delete()
        self.assertEqual(self.create(role='PSICOLOGO').status_code, 400)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(PerfilUsuario.objects.count(), 0)

    def test_filters_search_and_pagination(self):
        """Prepara persona por rol/estado y verifica búsquedas, catálogos, página vacía y rechazo
        de página cero.
        """
        created = self.create().data
        user = User.objects.get(pk=created['id'])
        user.is_active = False
        user.groups.set([Group.objects.get(name='TRABAJADOR')])
        user.save()
        for params in ({'role': 'TRABAJADOR'}, {'active': 'false'}, {'search': 'ANA.PRUEBA@'},
                       {'search': 'SA-001'}, {'area': self.area.pk}, {'cargo': self.cargo.pk}):
            response = self.client.get('/api/superadmin/users/', params)
            self.assertEqual(response.data['count'], 1, params)
            self.assertEqual(response.data['results'][0]['id'], user.pk)
        self.assertEqual(self.client.get('/api/superadmin/users/', {'role': 'PSICOLOGO'}).data['count'], 0)
        self.assertEqual(self.client.get('/api/superadmin/users/', {'page': 2}).data['results'], [])
        self.assertEqual(self.client.get('/api/superadmin/users/', {'page': 0}).status_code, 400)

    def test_edit_person_preserves_generated_email_and_password(self):
        user_id = self.create().data['id']
        previous = User.objects.get(pk=user_id)
        response = self.client.patch(f'/api/superadmin/users/{user_id}/',
                                    {'telefono': '+591 123', 'first_name': 'Editada'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        user = User.objects.get(pk=user_id)
        self.assertEqual(user.first_name, 'Editada')
        self.assertEqual(user.email, previous.email)
        self.assertEqual(user.username, previous.username)
        self.assertEqual(user.password, previous.password)
        self.assertEqual(user.perfil_usuario.telefono, '+591 123')
        self.assertEqual(self.login(user.email).status_code, 200)
        for field in ('email', 'username'):
            self.assertEqual(self.client.patch(f'/api/superadmin/users/{user_id}/',
                                              {field: 'manual@saspel.com'}, format='json').status_code, 400)

    def test_edit_rejects_sensitive_fields_and_inactive_references(self):
        """Envía privilegios y datos sensibles por PATCH y selecciona área inactiva; las
        operaciones deben rechazarse.
        """
        user_id = self.create().data['id']
        for data in ({'role': 'ADMIN'}, {'password': PASSWORD}, {'is_active': False}, {'tamizaje_resuelto': True}, {'is_superuser': True}):
            self.assertEqual(self.client.patch(f'/api/superadmin/users/{user_id}/', data, format='json').status_code, 400)
        area = AreaInstitucional.objects.create(nombre='Inactiva', activo=False)
        self.assertEqual(self.create(codigo_empleado='NEW', area_id=area.pk).status_code, 400)
        self.assertEqual(self.client.patch(f'/api/superadmin/users/{user_id}/', {'area_id': area.pk}, format='json').status_code, 400)

    def test_deactivate_blocks_login_activate_restores(self):
        """Desactiva y reactiva una persona: cambia su acceso al login, conserva perfil y sigue
        sin permitir DELETE.
        """
        user_id = self.create().data['id']
        self.assertEqual(self.action(user_id, 'deactivate').status_code, 200)
        self.assertEqual(self.login().status_code, 403)
        self.assertEqual(self.action(user_id, 'activate').status_code, 200)
        self.assertEqual(self.login().status_code, 200)
        self.assertTrue(PerfilUsuario.objects.filter(usuario_id=user_id).exists())
        self.assertEqual(self.client.delete(f'/api/superadmin/users/{user_id}/').status_code, 405)

    def test_self_and_last_superadmin_protection(self):
        """Prueba autooperación y último Superadmin por separado; otro administrador sí puede
        desactivarse.
        """
        self.assertEqual(self.action(self.root.pk, 'deactivate').status_code, 400)
        self.assertEqual(self.action(self.root.pk, 'role', {'role': 'ADMIN'}).status_code, 400)
        # Se ejercita la regla del último activo separadamente de la autooperación.
        for case, args in ((DeactivateUser, (self.root.pk, -1)), (ChangeUserRole, (self.root.pk, 'ADMIN', -1))):
            with self.assertRaisesMessage(AdministrationError, 'al menos un SUPERADMIN'):
                build_administration(case).execute(*args)
        other = self.create(role='SUPERADMIN').data['id']
        self.assertEqual(self.action(other, 'deactivate').status_code, 200)

    def test_administrative_role_changes_and_no_worker_transition(self):
        """Recorre correcciones administrativas, comprueba flags/grupo único y rechaza
        promociones del nuevo trabajador.
        """
        user_id = self.create(role='PSICOLOGO').data['id']
        for role in ('ADMIN', 'PSICOLOGO', 'SUPERADMIN', 'ADMIN', 'NUEVO_TRABAJADOR'):
            response = self.action(user_id, 'role', {'role': role})
            self.assertEqual(response.status_code, 200, response.data)
            user = User.objects.get(pk=user_id)
            self.assertEqual(list(user.groups.values_list('name', flat=True)), [role])
            self.assertEqual(user.is_superuser, role == 'SUPERADMIN')
        for role in ('TRABAJADOR', 'ADMIN'):
            self.assertEqual(self.action(user_id, 'role', {'role': role}).status_code, 400)

    def test_reset_password_invalidates_old_password(self):
        """Restablece clave confirmada y comprueba que la anterior falle y la nueva permita login
        sin aparecer en la salida.
        """
        user_id = self.create().data['id']
        password = 'Renovada-clave-7482!'
        self.assertEqual(self.action(user_id, 'reset-password', {'password': password, 'password_confirmation': 'otra'}).status_code, 400)
        response = self.action(user_id, 'reset-password', {'password': password, 'password_confirmation': password})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(password, repr(response.data))
        self.assertEqual(self.login().status_code, 401)
        self.assertEqual(self.login(password=password).status_code, 200)

    def test_summary_uses_real_counts_and_recent_five(self):
        """Crea seis personas para comprobar totales reales y corte/orden de los cinco registros
        recientes.
        """
        for i in range(6):
            self.create(codigo_empleado=f'R-{i}')
        response = self.client.get('/api/superadmin/dashboard/summary/')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['users_total'], User.objects.count())
        self.assertEqual(response.data['new_workers'], 6)
        self.assertEqual(response.data['active_users'], 7)
        self.assertEqual(response.data['inactive_users'], 0)
        self.assertEqual(len(response.data['recent_users']), 5)
        self.assertEqual(response.data['recent_users'][0]['email'], 'ana.prueba6@saspel.com')

    def test_institution_crud_preserves_associated_profiles(self):
        """Crea, edita y cambia estados de catálogos; comprueba que se conserve la referencia del
        perfil y se rechace borrar.
        """
        user_id = self.create().data['id']
        for kind, item in (('areas', self.area), ('cargos', self.cargo)):
            base = f'/api/superadmin/{kind}/'
            self.assertEqual(self.client.post(base, {'nombre': 'Nueva'}, format='json').status_code, 201)
            self.assertEqual(self.client.get(base + f'{item.pk}/').status_code, 200)
            self.assertEqual(self.client.patch(base + f'{item.pk}/', {'descripcion': 'Editada'}, format='json').status_code, 200)
            self.assertEqual(self.client.post(base + f'{item.pk}/deactivate/').status_code, 200)
            self.assertEqual(len(self.client.get(base, {'active': 'true'}).data), 1)
            self.assertEqual(self.client.post(base + f'{item.pk}/activate/').status_code, 200)
            self.assertEqual(self.client.delete(base + f'{item.pk}/').status_code, 405)
        self.assertEqual(PerfilUsuario.objects.get(usuario_id=user_id).area_id, self.area.pk)

    def test_unknown_ids_are_404(self):
        """Consulta IDs ausentes de persona, área y cargo para proteger el contrato HTTP 404."""
        for url in ('users/999999/', 'areas/999999/', 'cargos/999999/'):
            self.assertEqual(self.client.get('/api/superadmin/' + url).status_code, 404)
