from typing import Protocol
from uuid import UUID

from src.application.dto.nuevo_trabajador import EvaluacionInicialDTO


class NuevoTrabajadorRepository(Protocol):
    def evaluacion_inicial(self, usuario_id: UUID) -> EvaluacionInicialDTO | None: ...
