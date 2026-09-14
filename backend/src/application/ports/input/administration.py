"""Describe las operaciones administrativas con contrato de entrada explícito: listado, detalle,
registro, edición, clave y resumen. Las vistas construyen sus casos mediante
dependencies/superadmin.py; las acciones de rol, estado y catálogos usan directamente sus
casos concretos.
"""

from typing import Protocol
from src.application.dto.superadmin import (
    CreateUserCommand, DashboardSummary, ResetPasswordCommand,
    UpdateUserCommand, UserDTO, UserFilters, UserPage,
)


class UserListing(Protocol):
    """Recibe filtros y devuelve una página de personas para el listado."""
    def execute(self, filters: UserFilters) -> UserPage: ...


class UserDetail(Protocol):
    """Recibe ID de cuenta y devuelve su ficha; cuenta inexistente produce PersonNotFound."""
    def execute(self, user_id: int) -> UserDTO: ...


class UserRegistration(Protocol):
    """Recibe CreateUserCommand y devuelve la cuenta creada con perfil y rol; los fallos deben
    revertir el alta.
    """
    def execute(self, command: CreateUserCommand) -> UserDTO: ...


class UserEdition(Protocol):
    """Recibe ID y cambios personales parciales; devuelve la ficha actualizada."""
    def execute(self, command: UpdateUserCommand) -> UserDTO: ...


class PasswordReset(Protocol):
    """Recibe clave confirmada e ID; guarda el hash y no devuelve datos de la clave."""
    def execute(self, command: ResetPasswordCommand) -> None: ...


class DashboardOverview(Protocol):
    """Devuelve totales y personas recientes para el inicio de Superadmin."""
    def execute(self) -> DashboardSummary: ...
