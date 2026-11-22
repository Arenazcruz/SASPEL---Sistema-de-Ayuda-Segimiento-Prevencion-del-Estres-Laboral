from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from src.domain.exceptions.evaluacion import EvaluacionError


@dataclass(frozen=True)
class ItemPuntaje:
    tipo_respuesta: str
    invertida: bool
    valor: Decimal
    valores_escala: tuple[Decimal, ...]


@dataclass(frozen=True)
class RangoPuntaje:
    id: UUID
    minimo: Decimal
    maximo: Decimal


def calcular_puntaje(items: tuple[ItemPuntaje, ...]) -> Decimal:
    if not items:
        raise EvaluacionError('No hay respuestas disponibles para calcular el resultado.')
    total = Decimal('0')
    for item in items:
        if (item.tipo_respuesta != 'ESCALA' or not item.valores_escala
                or any(not value.is_finite() for value in item.valores_escala)
                or not item.valor.is_finite() or item.valor not in item.valores_escala):
            raise EvaluacionError('La configuración de la evaluación no permite calcular el resultado.')
        total += (min(item.valores_escala) + max(item.valores_escala) - item.valor
                  if item.invertida else item.valor)
    if abs(total) >= Decimal('100000000'):
        raise EvaluacionError('El puntaje excede la capacidad configurada para el resultado.')
    return total


def seleccionar_rango(puntaje: Decimal, rangos: tuple[RangoPuntaje, ...]) -> UUID | None:
    matches = [r.id for r in rangos if r.minimo <= puntaje <= r.maximo]
    if len(matches) > 1:
        raise EvaluacionError('Hay varios rangos de interpretación coincidentes. Revisa la configuración.')
    return matches[0] if matches else None
