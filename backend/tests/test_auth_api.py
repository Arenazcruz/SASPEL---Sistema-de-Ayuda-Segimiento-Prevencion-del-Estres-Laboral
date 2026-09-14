"""Prueba el acceso real por correo y tokens con usuarios ficticios en la BD temporal."""

from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AuthApiTests(TestCase):
    """Prueba login, me, refresh y CORS usando Django, JWT y cuentas ficticias en BD temporal."""
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='persona@example.com', email='Persona@Example.com',
            password='Test-password-2026!', first_name='Ana', last_name='Prueba',
        )
        cls.user.groups.add(Group.objects.get(name='TRABAJADOR'))

    def setUp(self):
        self.client = APIClient()

    def login(self, **changes):
        """Devuelve respuesta de login con credenciales ficticias y cambios opcionales para
        escenarios de error.
        """
        data = {'email': 'PERSONA@example.COM', 'password': 'Test-password-2026!'}
        data.update(changes)
        return self.client.post('/api/auth/login/', data, format='json')

    def test_login_correcto_por_correo_sin_distinguir_mayusculas(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['id'], self.user.pk)
        self.assertEqual(response.data['dashboard_path'], '/dashboard/trabajador')
        self.assertEqual(response.data['user']['role'], 'TRABAJADOR')
        self.assertEqual(AccessToken(response.data['access'])['user_id'], str(self.user.pk))
        self.assertEqual(RefreshToken(response.data['refresh'])['user_id'], str(self.user.pk))
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertNotIn('password', response.data['user'])

    def test_password_incorrecto_y_correo_inexistente_mismo_error(self):
        """Compara fallos por correo y por clave para evitar revelar si una cuenta existe."""
        incorrect = self.login(password='incorrecta')
        unknown = self.login(email='nadie@example.com')
        self.assertEqual(incorrect.status_code, 401)
        self.assertEqual(unknown.status_code, 401)
        self.assertEqual(incorrect.data, unknown.data)
        self.assertEqual(str(incorrect.data['detail']), 'Correo o contraseña incorrectos.')

    def test_usuario_inactivo_con_clave_correcta_recibe_403(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.login().status_code, 403)
        self.assertEqual(self.login(password='incorrecta').status_code, 401)

    def test_correos_duplicados_no_eligen_una_cuenta_arbitraria(self):
        """Introduce correo duplicado para exigir rechazo del login aunque una clave sea
        correcta.
        """
        get_user_model().objects.create_user(username='duplicada', email='persona@example.com', password='otra')
        self.assertEqual(self.login().status_code, 401)

    def test_formato_invalido_recibe_400(self):
        self.assertEqual(self.login(email='no-es-correo').status_code, 400)
        self.assertEqual(self.login(password='').status_code, 400)

    def test_cada_grupo_redirige_a_su_panel(self):
        for role, path in (
            ('NUEVO_TRABAJADOR', 'nuevo-trabajador'), ('TRABAJADOR', 'trabajador'),
            ('PSICOLOGO', 'psicologo'), ('ADMIN', 'admin'), ('SUPERADMIN', 'superadmin'),
        ):
            with self.subTest(role=role):
                self.user.groups.set([Group.objects.get(name=role)])
                response = self.login()
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data['user']['role'], role)
                self.assertEqual(response.data['dashboard_path'], '/dashboard/' + path)

    def test_superuser_es_superadmin_incluso_sin_grupo(self):
        self.user.is_superuser = True
        self.user.save()
        self.assertEqual(self.login().data['user']['role'], 'SUPERADMIN')

    def test_sin_rol_no_emite_tokens(self):
        self.user.groups.clear()
        response = self.login()
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('access', response.data)

    def test_me_sin_token_recibe_401(self):
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)

    def test_me_con_token_devuelve_identidad_actual_y_no_rol_del_cliente(self):
        """Cambia el grupo después del login y reutiliza el token; me debe devolver el rol
        actualizado desde la cuenta.
        """
        access = self.login().data['access']
        self.user.groups.set([Group.objects.get(name='PSICOLOGO')])
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access)
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['role'], 'PSICOLOGO')
        self.assertEqual(response.data['dashboard_path'], '/dashboard/psicologo')

    def test_me_rechaza_token_expirado_o_manipulado(self):
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=timedelta(seconds=-1))
        for value in (str(token), 'token-manipulado'):
            self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + value)
            self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)

    def test_refresh_valido(self):
        response = self.client.post('/api/auth/refresh/', {'refresh': self.login().data['refresh']}, format='json')
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['access'])
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 200)

    def test_refresh_invalido_expirado_o_de_tipo_access(self):
        expired = RefreshToken.for_user(self.user)
        expired.set_exp(lifetime=timedelta(seconds=-1))
        for value in ('invalido', str(expired), str(AccessToken.for_user(self.user))):
            response = self.client.post('/api/auth/refresh/', {'refresh': value}, format='json')
            self.assertEqual(response.status_code, 401)

    def test_refresh_rechaza_cuenta_desactivada_y_borrada(self):
        """Conserva refresh mientras cambia la cuenta; una sesión ya sin cuenta activa no debe
        renovarse.
        """
        refresh = str(RefreshToken.for_user(self.user))
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.client.post('/api/auth/refresh/', {'refresh': refresh}).status_code, 401)
        self.user.delete()
        self.assertEqual(self.client.post('/api/auth/refresh/', {'refresh': refresh}).status_code, 401)

    def test_login_ignora_authorization_anterior(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer token-viejo')
        self.assertEqual(self.login().status_code, 200)

    def test_cors_permite_solo_origenes_configurados(self):
        for origin in ('http://localhost:4200', 'http://127.0.0.1:4200'):
            response = self.client.options('/api/auth/login/', HTTP_ORIGIN=origin, HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST')
            self.assertEqual(response['Access-Control-Allow-Origin'], origin)
        response = self.client.options('/api/auth/login/', HTTP_ORIGIN='https://otro.example', HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST')
        self.assertNotIn('Access-Control-Allow-Origin', response)
