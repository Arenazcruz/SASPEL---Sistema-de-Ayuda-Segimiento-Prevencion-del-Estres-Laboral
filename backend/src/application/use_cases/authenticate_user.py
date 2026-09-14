"""Login de LoginView: delega credenciales a infrastructure/auth y panel a
services/auth_identity.
"""

from src.application.dto.auth import AuthenticatedUserDTO, LoginCommand
from src.application.ports.output.auth_provider import AuthProvider
from src.application.services.auth_identity import present_identity


class AuthenticateUser:
    """Recibe AuthProvider; la emisión JWT queda en la vista."""
    def __init__(self, provider: AuthProvider):
        self.provider = provider

    def execute(self, command: LoginCommand) -> AuthenticatedUserDTO:
        """Recibe LoginCommand, quita espacios del correo y devuelve AuthenticatedUserDTO con rol
        y panel. Propaga credenciales inválidas, cuenta inactiva o falta de rol. El proveedor
        Django actual actualiza last_login; la vista emite los tokens después.
        """
        identity = self.provider.authenticate(command.email.strip(), command.password)
        return present_identity(identity)
