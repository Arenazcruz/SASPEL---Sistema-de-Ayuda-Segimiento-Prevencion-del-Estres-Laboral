from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PoliticaDTO:
    id: UUID
    tipo: str
    titulo: str
    version: str
    contenido: str
    vigente_desde: datetime
    obligatoria: bool
    activo: bool


@dataclass(frozen=True)
class CuentaPrimerAcceso:
    role: str
    dashboard_path: str
    debe_cambiar_password: bool


@dataclass(frozen=True)
class EstadoPrimerAcceso:
    debe_cambiar_password: bool
    politicas_pendientes: tuple[UUID, ...]
    completo: bool
    siguiente_ruta: str


@dataclass(frozen=True)
class CambiarPasswordCommand:
    usuario_id: UUID
    password: str = field(repr=False)
    password_confirmation: str = field(repr=False)


@dataclass(frozen=True)
class AceptarPoliticasCommand:
    usuario_id: UUID
    politicas: tuple[UUID, ...]
