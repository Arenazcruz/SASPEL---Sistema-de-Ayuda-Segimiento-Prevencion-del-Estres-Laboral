"""Contratos de administración de instrumentos, independientes de HTTP y ORM."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class InstrumentData:
    codigo: str
    nombre: str
    version: str = '1.0'
    descripcion: str = ''
    instrucciones: str = ''
    es_inicial: bool = False


@dataclass(frozen=True)
class InstrumentDTO:
    id: UUID
    codigo: str
    nombre: str
    version: str
    descripcion: str
    instrucciones: str
    es_inicial: bool
    activo: bool
    creado_en: datetime
    actualizado_en: datetime


@dataclass(frozen=True)
class InstrumentFilters:
    search: str = ''
    activo: bool | None = None
    es_inicial: bool | None = None
    page: int = 1


@dataclass(frozen=True)
class InstrumentPage:
    count: int
    page: int
    page_size: int
    results: list[InstrumentDTO]
