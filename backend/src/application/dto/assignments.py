"""Contratos de T23: identidades mínimas, filtros y comandos sin detalles HTTP ni ORM."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AssignmentPerson:
    """Datos de selección y elegibilidad; no expone claves ni información clínica."""
    id: int
    nombre_completo: str
    email: str
    codigo_empleado: str
    role: str | None
    is_active: bool
    habilitado_asignaciones: bool


@dataclass(frozen=True)
class AssignmentDTO:
    """Vínculo vigente o histórico; fecha_fin y motivo_fin describen su cierre."""
    id: int
    trabajador: AssignmentPerson
    psicologo: AssignmentPerson
    fecha_asignacion: datetime
    fecha_fin: datetime | None
    estado: str
    motivo_fin: str


@dataclass(frozen=True)
class AssignmentFilters:
    """Estado vacío incluye historial; trabajador_id permite consultar una persona."""
    estado: str = ''
    trabajador_id: int | None = None
    psicologo_id: int | None = None
    search: str = ''
    page: int = 1


@dataclass(frozen=True)
class AssignmentPage:
    count: int
    page: int
    page_size: int
    results: list[AssignmentDTO]


@dataclass(frozen=True)
class WorkerPage:
    count: int
    page: int
    page_size: int
    results: list[AssignmentPerson]


@dataclass(frozen=True)
class PsychologistLoad:
    """Cantidad de vínculos ACTIVA, incluso si el trabajador perdió acceso a su cuenta."""
    psicologo: AssignmentPerson
    trabajadores_activos: int


@dataclass(frozen=True)
class AssignWorkerCommand:
    trabajador_id: int
    psicologo_id: int


@dataclass(frozen=True)
class FinishAssignmentCommand:
    asignacion_id: int
    motivo_fin: str


@dataclass(frozen=True)
class ReassignWorkerCommand:
    asignacion_id: int
    psicologo_id: int
    motivo_fin: str
