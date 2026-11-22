import os
from pathlib import Path
import secrets
import subprocess
from unittest import skipUnless
from unittest.mock import patch
from django.core.management import call_command
from django.test import LiveServerTestCase
from src.infrastructure.persistence.django import models as m


@skipUnless(os.getenv('SASPEL_BROWSER_TEST')=='1', 'Ensayo con Edge y PostgreSQL aislado.')
class EnsayoDemoTests(LiveServerTestCase):
    def test_guion_demostrado_con_cinco_roles(self):
        secret=secrets.token_hex(14)+'Az9!'
        with patch.dict(os.environ, {'SASPEL_DEMO_PASSWORD':secret}):
            call_command('seed_demo')
            run=subprocess.run(['node',str(Path(__file__).resolve().parents[2]/'frontend/e2e/ensayo.cjs')],
                env=dict(os.environ,SASPEL_TEST_API=self.live_server_url),capture_output=True,
                encoding='utf8',timeout=180)
        self.assertEqual(run.returncode,0,(run.stdout+run.stderr).replace(secret,'[redactado]'))
        self.assertTrue(m.Usuario.objects.get(email='demo.nuevo@saspel.com').groups.filter(name='TRABAJADOR').exists())
        self.assertEqual(m.Cita.objects.get().estado,'CONFIRMADA')
        self.assertEqual(m.ResultadoInstrumento.objects.count(),3)
