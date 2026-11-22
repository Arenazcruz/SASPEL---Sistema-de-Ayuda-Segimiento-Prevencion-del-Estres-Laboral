import os
from unittest.mock import patch
from django.apps import apps
from django.core.management import call_command
from django.test import TestCase
from src.infrastructure.persistence.django import models as m


class DemoTests(TestCase):
    @patch.dict(os.environ, {'SASPEL_DEMO_PASSWORD':'SoloPruebas-local-123'})
    def test_repeticion_conserva_cuentas_eventos_y_resultados(self):
        def cantidades():
            return {model._meta.label:model.objects.count() for model in apps.get_app_config('api').get_models()}
        call_command('seed_demo')
        first = cantidades()
        call_command('seed_demo')
        self.assertEqual(cantidades(),first)
        self.assertEqual(m.Usuario.objects.count(),5)
        self.assertEqual(m.ResultadoInstrumento.objects.count(),2)
        self.assertEqual(m.Alerta.objects.count(),2)
        self.assertTrue(m.Notificacion.objects.filter(tipo='RECOMENDACION').exists())
        self.assertEqual(m.Recomendacion.objects.filter(compartida=True).count(),1)
