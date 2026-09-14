"""Comprueba la elección de paneles sin cargar Django ni acceder a una base de datos."""

from unittest import TestCase
from src.application.dto.auth import AuthIdentity, LoginCommand
from src.application.services.auth_identity import MissingFunctionalRole, present_identity
from src.application.use_cases.authenticate_user import AuthenticateUser
from src.application.use_cases.get_authenticated_user import GetAuthenticatedUser


class FakeProvider:
    """Doble de AuthProvider con identidad configurable; permite probar delegación y roles sin
    Django.
    """
    def __init__(self, groups=('TRABAJADOR',), superuser=False):
        self.identity = AuthIdentity(1, 'test@example.com', 'Ana', 'Prueba', groups, superuser)

    def authenticate(self, email, password):
        """Registra credenciales recibidas y devuelve identidad ficticia; no verifica hashes
        reales.
        """
        self.credentials = (email, password)
        return self.identity

    def get_identity(self, user_id):
        """Devuelve la identidad ficticia para aislar la resolución de roles del almacenamiento."""
        self.requested_id = user_id
        return self.identity


class AuthUseCaseTests(TestCase):
    """Prueba login/me y precedencia de roles sin base de datos."""
    def test_login_delega_credenciales_y_devuelve_dto(self):
        """Comprueba que login delegue al proveedor y presente el DTO de identidad."""
        provider = FakeProvider()
        result = AuthenticateUser(provider).execute(LoginCommand(' test@example.com ', 'test-password'))
        self.assertEqual(provider.credentials, ('test@example.com', 'test-password'))
        self.assertEqual(result.dashboard_path, '/dashboard/trabajador')
        self.assertNotIn('test-password', repr(LoginCommand('test@example.com', 'test-password')))

    def test_cada_rol_tiene_su_panel(self):
        for role, path in (
            ('NUEVO_TRABAJADOR', '/dashboard/nuevo-trabajador'),
            ('TRABAJADOR', '/dashboard/trabajador'), ('PSICOLOGO', '/dashboard/psicologo'),
            ('ADMIN', '/dashboard/admin'), ('SUPERADMIN', '/dashboard/superadmin'),
        ):
            with self.subTest(role=role):
                user = present_identity(FakeProvider((role,)).identity)
                self.assertEqual(user.role, role)
                self.assertEqual(user.dashboard_path, path)

    def test_prioridad_de_roles_es_independiente_del_orden_de_grupos(self):
        """Añade grupos de mayor prioridad al final para comprobar que no gane el primero
        recibido del proveedor.
        """
        roles = ['NUEVO_TRABAJADOR', 'TRABAJADOR', 'PSICOLOGO', 'ADMIN', 'SUPERADMIN']
        for count in range(1, 6):
            self.assertEqual(present_identity(FakeProvider(tuple(roles[:count])).identity).role, roles[count - 1])

    def test_superuser_tiene_prioridad(self):
        self.assertEqual(present_identity(FakeProvider(('TRABAJADOR',), True).identity).role, 'SUPERADMIN')

    def test_cuenta_sin_rol_conocido_no_recibe_privilegios(self):
        """Entrega una identidad sin rol funcional reconocido y exige MissingFunctionalRole."""
        with self.assertRaises(MissingFunctionalRole):
            present_identity(FakeProvider(('OTRO',)).identity)

    def test_recupera_identidad_actual(self):
        provider = FakeProvider(('PSICOLOGO',))
        user = GetAuthenticatedUser(provider).execute(1)
        self.assertEqual(provider.requested_id, 1)
        self.assertEqual(user.role, 'PSICOLOGO')
