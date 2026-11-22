"""Pruebas focalizadas del límite de fallos, sin esperas ni navegador."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import caches
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from src.infrastructure.auth.login_attempts import LoginAttemptBudget


@override_settings(
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    CACHES={
        'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
        'login_attempts': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'saspel-login-limit-tests',
        },
    },
)
class LoginAttemptTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = 'Prueba-segura-2026!'
        cls.user = get_user_model().objects.create_user(
            username='persona@saspel.com', email='persona@saspel.com', password=cls.password,
        )
        cls.user.groups.add(Group.objects.get(name='TRABAJADOR'))

    def setUp(self):
        caches['login_attempts'].clear()
        self.addCleanup(caches['login_attempts'].clear)
        self.clock_patch = patch('src.infrastructure.auth.login_attempts.time', return_value=1_800_000_010)
        self.clock = self.clock_patch.start()
        self.addCleanup(self.clock_patch.stop)
        self.client = APIClient()

    def login(self, email='persona@saspel.com', password=None, ip='192.0.2.1', **headers):
        return self.client.post('/api/auth/login/', {
            'email': email, 'password': self.password if password is None else password,
        }, format='json', REMOTE_ADDR=ip, **headers)

    def fail(self, **kwargs):
        return self.login(password='incorrecta', **kwargs)

    def test_normal_attempts_and_repeated_successes_are_allowed(self):
        self.assertEqual(self.fail().status_code, 401)
        for _ in range(8):
            response = self.login()
            self.assertEqual(response.status_code, 200)
            self.assertIn('access', response.data)
            self.assertIn('refresh', response.data)

    def test_repeated_failures_block_even_correct_password_without_modifying_user(self):
        old_hash = self.user.password
        for index in range(5):
            # Mayúsculas, espacios e IP distinta no evitan el límite por correo.
            response = self.fail(email=' PERSONA@SASPEL.COM ', ip=f'192.0.2.{index + 1}')
            self.assertEqual(response.status_code, 401)
        with patch('src.infrastructure.api.rest.views.auth.build_authentication') as authentication:
            response = self.login()
            authentication.assert_not_called()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.data, {'detail': 'Credenciales no válidas.'})
        self.assertEqual(response['Retry-After'], '290')
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertEqual(self.user.password, old_hash)
        self.assertIsNone(self.user.last_login)
        self.assertEqual(list(self.user.groups.values_list('name', flat=True)), ['TRABAJADOR'])

    def test_block_expires_and_blocked_requests_do_not_extend_it(self):
        for _ in range(5):
            self.fail()
        self.clock.return_value = 1_800_000_100
        self.assertEqual(self.login()['Retry-After'], '200')
        self.clock.return_value = 1_800_000_299
        self.assertEqual(self.login().status_code, 429)
        self.clock.return_value = 1_800_000_300
        self.assertEqual(self.login().status_code, 200)

    def test_active_and_inactive_accounts_keep_their_responses(self):
        self.assertEqual(self.login().status_code, 200)
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        self.assertEqual(self.fail().status_code, 401)
        response = self.login()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, {'detail': 'Esta cuenta no está habilitada para ingresar.'})
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])
        self.assertEqual(self.login().status_code, 200)

    def test_known_unknown_and_external_accounts_share_limit_and_generic_error(self):
        for email in ('persona@saspel.com', 'ausente@saspel.com', 'externa@example.com'):
            for _ in range(5):
                response = self.fail(email=email)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.data, {'detail': 'Credenciales no válidas.'})
            response = self.fail(email=email)
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.data, {'detail': 'Credenciales no válidas.'})

    def test_ip_limit_cannot_be_bypassed_by_rotating_emails_or_forwarded_headers(self):
        for index in range(20):
            self.assertEqual(self.fail(email=f'ausente{index}@saspel.com').status_code, 401)
        self.assertEqual(self.login(HTTP_X_FORWARDED_FOR='198.51.100.9').status_code, 429)
        self.assertEqual(self.login(ip='192.0.2.2').status_code, 200)

    def test_success_does_not_erase_previous_failed_attempts(self):
        for _ in range(4):
            self.fail()
        self.assertEqual(self.login().status_code, 200)
        self.assertEqual(self.fail().status_code, 401)
        self.assertEqual(self.login().status_code, 429)

    def test_server_errors_do_not_consume_failed_login_budget(self):
        with patch('src.infrastructure.api.rest.views.auth.build_authentication', side_effect=RuntimeError('test')):
            for _ in range(6):
                with self.assertRaises(RuntimeError):
                    self.login()
        self.assertEqual(self.login().status_code, 200)

    def test_concurrent_attempts_cannot_overbook_email_budget(self):
        start = Barrier(10)

        def reserve(index):
            start.wait(timeout=10)
            return LoginAttemptBudget('persona@saspel.com', f'192.0.2.{index}').reserve()

        with ThreadPoolExecutor(max_workers=10) as pool:
            admitted = list(pool.map(reserve, range(10)))
        self.assertEqual(sum(admitted), 5)
