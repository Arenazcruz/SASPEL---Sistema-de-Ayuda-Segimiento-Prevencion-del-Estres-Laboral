"""Comprueba que el caso de uso de salud puede ejecutarse. No consulta PostgreSQL ni servicios
externos; la vista health transforma el resultado a JSON.
"""

from src.application.dto.health import HealthResult
from src.application.ports.input.health import HealthCheck


class GetHealthStatus(HealthCheck):
    """Prueba de ejecución del núcleo; no comprueba servicios externos."""

    def execute(self) -> HealthResult:
        """Devuelve el estado fijo de ejecución del núcleo, sin leer ni modificar datos."""
        return HealthResult(status='ok', architecture='hexagonal')
