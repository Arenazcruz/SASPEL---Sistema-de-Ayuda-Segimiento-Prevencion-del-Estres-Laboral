from typing import Protocol
from uuid import UUID

from src.application.dto.nuevo_trabajador import DashboardNuevoTrabajadorDTO


class DashboardNuevoTrabajador(Protocol):
    def execute(self, usuario_id: UUID) -> DashboardNuevoTrabajadorDTO: ...
