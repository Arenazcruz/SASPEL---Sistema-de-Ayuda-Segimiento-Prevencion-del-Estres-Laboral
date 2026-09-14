"""Prueba el resultado de salud sin Django ni persistencia; protege el contrato fijo del caso
GetHealthStatus.
"""

from unittest import TestCase

from src.application.dto.health import HealthResult
from src.application.use_cases.health import GetHealthStatus


class HealthUseCaseTests(TestCase):
    """Chequeo unitario del caso de salud."""
    def test_returns_health_without_framework_or_persistence(self):
        """Ejecuta el caso directamente y compara status/architecture sin levantar servicios."""
        self.assertEqual(
            GetHealthStatus().execute(),
            HealthResult(status='ok', architecture='hexagonal'),
        )
