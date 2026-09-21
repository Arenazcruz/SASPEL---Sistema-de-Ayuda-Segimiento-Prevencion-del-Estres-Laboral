"""Flujo real en navegador contra LiveServer y la base temporal de Django.

Requiere Angular en SASPEL_FRONTEND_URL (por defecto localhost:4200), Playwright
en SASPEL_PLAYWRIGHT_MODULE y SASPEL_BROWSER_TEST=1. No usa cuentas locales.
"""

import os
from pathlib import Path
import secrets
import subprocess
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import LiveServerTestCase, override_settings


@skipUnless(os.getenv('SASPEL_BROWSER_TEST') == '1', 'Prueba de navegador optativa; requiere Angular y Playwright.')
@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class UnifiedUsersBrowserTests(LiveServerTestCase):
    def test_unified_table_modals_and_login(self):
        password = secrets.token_urlsafe(24) + 'A9'
        user = get_user_model().objects.create_user(
            username='browser.admin@example.com', email='browser.admin@example.com',
            password=password, is_staff=True, is_superuser=True,
        )
        for name in ('SUPERADMIN', 'ADMIN', 'PSICOLOGO', 'NUEVO_TRABAJADOR', 'TRABAJADOR'):
            Group.objects.get_or_create(name=name)
        user.groups.add(Group.objects.get(name='SUPERADMIN'))
        root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            ['node', str(root / 'frontend/e2e/unified-users.cjs')],
            env=dict(os.environ, SASPEL_TEST_API=self.live_server_url,
                     SASPEL_TEST_EMAIL=user.email, SASPEL_TEST_PASSWORD=password),
            capture_output=True, text=True, encoding='utf-8', timeout=150,
        )
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr).replace(password, '[REDACTED]'))
        created = get_user_model().objects.get(email='jesus.cruz@saspel.com')
        self.assertTrue(created.is_active)
        self.assertEqual(created.username, created.email)
        self.assertEqual(created.perfil_usuario.telefono, '59170000000')
        self.assertTrue(created.check_password(password))
        self.assertTrue(created.groups.filter(name='NUEVO_TRABAJADOR').exists())
