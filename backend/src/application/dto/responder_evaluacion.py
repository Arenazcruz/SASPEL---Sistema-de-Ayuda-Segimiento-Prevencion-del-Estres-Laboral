from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class OpcionEvaluacion:
    id: UUID
    etiqueta: str


@dataclass(frozen=True)
class PreguntaEvaluacion:
    id: UUID
    texto: str
    orden: int
    tipo_respuesta: str
    obligatoria: bool
    opciones: tuple[OpcionEvaluacion, ...] = ()


@dataclass(frozen=True)
class RespuestaEvaluacion:
    pregunta_id: UUID
    opcion_id: UUID | None = None
    valor_texto: str | None = None
    valor_numerico: str | None = None
    valor_booleano: bool | None = None


@dataclass(frozen=True)
class EvaluacionDetalle:
    asignacion_id: UUID
    instrumento_id: UUID
    nombre: str
    version: str
    instrucciones: str
    estado_asignacion: str
    aplicacion_id: UUID | None
    estado_aplicacion: str | None
    fecha_inicio: datetime | None
    fecha_finalizacion: datetime | None
    disponible: bool
    preguntas: tuple[PreguntaEvaluacion, ...]
    respuestas: tuple[RespuestaEvaluacion, ...]


@dataclass(frozen=True)
class ResultadoEvaluacion:
    aplicacion_id: UUID
    instrumento_id: UUID
    nombre: str
    version: str
    fecha_calculo: datetime
    puntaje_total: str
    rango: str | None
    interpretacion: str
    tamizaje_resuelto: bool
    nuevo_rol: str
    dashboard_path: str
    estado_asignacion_profesional: str
