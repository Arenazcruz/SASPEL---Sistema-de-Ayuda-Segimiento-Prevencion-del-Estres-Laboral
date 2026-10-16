from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ResultadoResumen:
    id: UUID
    instrumento: str
    version: str
    fecha: datetime
    puntaje: str
    rango: str | None
    interpretacion: str
    estado: str


@dataclass(frozen=True)
class TrabajadorAsignado:
    id: UUID
    nombre_completo: str
    email: str
    area: str
    cargo: str
    fecha_asignacion: datetime
    estado: str


@dataclass(frozen=True)
class MisTrabajadores:
    cantidad: int
    trabajadores: tuple[TrabajadorAsignado, ...]
