"""Prueba /api/health/ y la respuesta histórica /api/. SimpleTestCase prohíbe consultas a BD:
estos endpoints solo comprueban ejecución y transporte.
"""

from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import reverse

from src.application.dto.health import HealthResult


class HealthApiTests(SimpleTestCase):
    # SimpleTestCase impide consultas a BD: solo se comprueba que la aplicación responde.
    """Contratos HTTP de prueba y salud sin depender de PostgreSQL."""
    def test_health_returns_expected_json(self):
        """Comprueba ruta, estado y JSON público del chequeo de salud."""
        self.assertEqual(reverse('health'), '/api/health/')
        response = self.client.get('/api/health/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json(), {
            'status': 'ok',
            'architecture': 'hexagonal',
        })

    def test_rest_adapter_uses_the_injected_input_port(self):
        """Sustituye la factoría para comprobar que la vista publica el resultado del caso
        inyectado.
        """
        with patch(
            'src.infrastructure.api.rest.views.health.build_health_check'
        ) as factory:
            factory.return_value.execute.return_value = HealthResult(
                status='test', architecture='substitute',
            )
            response = self.client.get('/api/health/')

        factory.assert_called_once_with()
        factory.return_value.execute.assert_called_once_with()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'status': 'test',
            'architecture': 'substitute',
        })

    def test_health_rejects_post(self):
        """Envía POST al chequeo de lectura para proteger su respuesta 405."""
        self.assertEqual(self.client.post('/api/health/').status_code, 405)

    def test_existing_api_response_is_preserved(self):
        """Comprueba que /api/ conserve el mensaje histórico de conexión con Django."""
        response = self.client.get('/api/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'mensaje': 'Django funciona'})
