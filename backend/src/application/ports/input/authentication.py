"""Contratos de sesión ofrecidos a las vistas; dependencies/auth.py conecta sus implementaciones."""

from typing import Protocol
from uuid import UUID
from src.application.dto.auth import AuthenticatedUserDTO, LoginCommand


class Authentication(Protocol):
    """LoginCommand entra; AuthenticatedUserDTO o una excepción de autenticación sale."""
    def execute(self, command: LoginCommand) -> AuthenticatedUserDTO: ...


class CurrentIdentity(Protocol):
    """El ID autenticado se transforma en identidad y rol vigentes."""
    def execute(self, user_id: UUID) -> AuthenticatedUserDTO: ...
