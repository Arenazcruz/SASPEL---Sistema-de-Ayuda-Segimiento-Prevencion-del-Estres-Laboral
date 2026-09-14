"""Respuesta interna del chequeo de salud; la vista publica estos valores como JSON. No
representa el estado de la conexión a PostgreSQL.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthResult:
    """Resultado técnico de la aplicación, independiente del transporte."""

    status: str
    architecture: str
