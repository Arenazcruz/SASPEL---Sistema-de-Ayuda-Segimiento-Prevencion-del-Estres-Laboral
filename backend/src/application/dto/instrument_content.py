"""Contratos UUID del contenido administrable de T25."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

ContentKind = Literal['questions', 'scales', 'options', 'ranges']


@dataclass(frozen=True)
class QuestionData:
    texto: str
    orden: int
    tipo_respuesta: str
    escala_id: UUID | None = None
    obligatoria: bool = True
    invertida: bool = False


@dataclass(frozen=True)
class ScaleData:
    nombre: str
    descripcion: str = ''


@dataclass(frozen=True)
class OptionData:
    etiqueta: str
    valor: int
    orden: int


@dataclass(frozen=True)
class RangeData:
    nombre: str
    puntaje_minimo: int
    puntaje_maximo: int
    orden: int
    interpretacion: str = ''


@dataclass(frozen=True)
class ContentDTO:
    id: UUID
    activo: bool
    creado_en: datetime
    actualizado_en: datetime


@dataclass(frozen=True)
class QuestionDTO(ContentDTO):
    instrumento_id: UUID
    texto: str
    orden: int
    tipo_respuesta: str
    escala_id: UUID | None
    obligatoria: bool
    invertida: bool


@dataclass(frozen=True)
class ScaleDTO(ContentDTO):
    nombre: str
    descripcion: str


@dataclass(frozen=True)
class OptionDTO(ContentDTO):
    escala_id: UUID
    etiqueta: str
    valor: int
    orden: int


@dataclass(frozen=True)
class RangeDTO(ContentDTO):
    instrumento_id: UUID
    nombre: str
    puntaje_minimo: int
    puntaje_maximo: int
    orden: int
    interpretacion: str


ContentData = QuestionData | ScaleData | OptionData | RangeData
ContentRecord = QuestionDTO | ScaleDTO | OptionDTO | RangeDTO


@dataclass(frozen=True)
class ContentFilters:
    search: str = ''
    activo: bool | None = None
    page: int = 1


@dataclass(frozen=True)
class ContentPage:
    count: int
    page: int
    page_size: int
    results: list[ContentRecord]
