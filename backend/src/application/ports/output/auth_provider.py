"""Contrato que permite cambiar DjangoAuthProvider sin cambiar los casos de sesión."""

from typing import Protocol
from src.application.dto.auth import AuthIdentity


class AuthProvider(Protocol):
    """Obtiene identidad; Application decide rol y la vista emite tokens."""
    # Correo/clave -> identidad o error; Django actualiza last_login al autenticar.
    def authenticate(self, email: str, password: str) -> AuthIdentity: ...

    # ID -> identidad actual o error por cuenta ausente/inactiva; sin escrituras.
    def get_identity(self, user_id: int) -> AuthIdentity: ...
