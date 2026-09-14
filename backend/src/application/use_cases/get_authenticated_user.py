"""Consulta identidad vigente para GET /api/auth/me/; el ID viene de la cuenta validada por JWT."""

from src.application.dto.auth import AuthenticatedUserDTO
from src.application.ports.output.auth_provider import AuthProvider
from src.application.services.auth_identity import present_identity


class GetAuthenticatedUser:
    """Reutiliza AuthProvider y la resolución de panel del login."""
    def __init__(self, provider: AuthProvider):
        self.provider = provider

    def execute(self, user_id: int) -> AuthenticatedUserDTO:
        """Recibe el ID de la cuenta y devuelve su identidad con rol y panel actuales. No escribe
        datos; propaga cuenta inexistente, inactiva o sin rol. Revisar junto al login si
        cambia la información de sesión.
        """
        return present_identity(self.provider.get_identity(user_id))
