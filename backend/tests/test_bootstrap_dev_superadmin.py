"""Comprueba que el comando local prepare una sola cuenta y nunca guarde la clave literal."""

from io import StringIO
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings


@override_settings(DEBUG=True, PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BootstrapDevSuperadminTests(TestCase):
    """Prueba el comando local con entorno ficticio y hash rápido, sin modificar .env."""
    def run_command(self):
        """Sustituye variables del proceso, ejecuta bootstrap en BD de pruebas y devuelve stdout
        capturado; restaura entorno al salir.
        """
        output = StringIO()
        with patch.dict('os.environ', {
            'SASPEL_DEV_SUPERADMIN_EMAIL': 'Admin-Test@Example.com',
            'SASPEL_DEV_SUPERADMIN_PASSWORD': 'Only-for-tests-2026!',
        }):
            call_command('bootstrap_dev_superadmin', stdout=output)
        return output.getvalue()

    def test_crea_cuenta_con_clave_hasheada_y_grupo_superadmin(self):
        output = self.run_command()
        user = get_user_model().objects.get()
        self.assertEqual(user.username, 'admin-test@example.com')
        self.assertEqual(user.email, user.username)
        self.assertTrue(user.is_staff and user.is_superuser and user.is_active)
        self.assertTrue(user.groups.filter(name='SUPERADMIN').exists())
        self.assertTrue(user.check_password('Only-for-tests-2026!'))
        self.assertNotEqual(user.password, 'Only-for-tests-2026!')
        self.assertNotIn('Only-for-tests-2026!', output)
        self.assertIn('creada', output)

    def test_idempotente_actualiza_sin_duplicar(self):
        self.run_command()
        user_id = get_user_model().objects.get().pk
        self.assertIn('actualizada', self.run_command())
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(get_user_model().objects.get().pk, user_id)

    @override_settings(DEBUG=False)
    def test_no_funciona_fuera_de_desarrollo(self):
        with self.assertRaises(CommandError):
            self.run_command()
        self.assertFalse(get_user_model().objects.exists())

    def test_faltan_variables_no_crea_cuenta(self):
        with patch.dict('os.environ', {'SASPEL_DEV_SUPERADMIN_EMAIL': '', 'SASPEL_DEV_SUPERADMIN_PASSWORD': ''}):
            with self.assertRaises(CommandError):
                call_command('bootstrap_dev_superadmin')
        self.assertFalse(get_user_model().objects.exists())

    def test_conflicto_username_no_promueve_otra_cuenta(self):
        """Ocupa username con otro correo y comprueba que el comando no eleve privilegios de esa
        cuenta.
        """
        user = get_user_model().objects.create_user(username='admin-test@example.com', email='otra@example.com')
        with self.assertRaises(CommandError):
            self.run_command()
        user.refresh_from_db()
        self.assertFalse(user.is_superuser)
