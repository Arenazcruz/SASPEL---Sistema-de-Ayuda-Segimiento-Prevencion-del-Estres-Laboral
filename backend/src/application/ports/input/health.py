"""Puerto del chequeo de ejecución; dependencies/health.py conecta GetHealthStatus."""

from typing import Protocol

from src.application.dto.health import HealthResult


class HealthCheck(Protocol):
    """Permite a la vista pedir salud sin conocer el caso concreto."""

    def execute(self) -> HealthResult:
        """Devuelve HealthResult; no comprueba PostgreSQL ni servicios externos."""
        ...
