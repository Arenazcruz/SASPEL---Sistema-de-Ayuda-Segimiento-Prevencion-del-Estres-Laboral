"""Conecta la vista de salud con GetHealthStatus. Cambiar aquí la implementación mantiene el
puerto HealthCheck disponible para el adaptador HTTP.
"""

from src.application.ports.input.health import HealthCheck
from src.application.use_cases.health import GetHealthStatus


def build_health_check() -> HealthCheck:
    """Devuelve el caso del chequeo de ejecución; no consulta servicios al construirlo."""
    return GetHealthStatus()
