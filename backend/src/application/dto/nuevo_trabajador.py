from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID


@dataclass(frozen=True)
class EvaluacionInicialDTO:
    estado: Literal['SIN_ASIGNAR', 'PENDIENTE', 'EN_PROGRESO', 'COMPLETADA']
    asignacion_id: UUID | None = None
    instrumento_id: UUID | None = None
    nombre: str | None = None
    version: str | None = None
    fecha_asignacion: datetime | None = None
    fecha_limite: datetime | None = None


@dataclass(frozen=True)
class DashboardNuevoTrabajadorDTO:
    evaluacion_inicial: EvaluacionInicialDTO
