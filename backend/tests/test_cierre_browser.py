"""Integración Angular/API real con cuentas y registros exclusivamente sintéticos."""
import json
import os
from pathlib import Path
import secrets
import subprocess
from unittest import skipUnless
from django.test import LiveServerTestCase, override_settings
from tests import test_cierre_funcional as fixtures
from src.infrastructure.persistence.django.models import ResultadoInstrumento, Recomendacion


@skipUnless(os.getenv('SASPEL_BROWSER_TEST') == '1', 'Requiere --browser, Angular y Playwright.')
@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CierreBrowserTests(LiveServerTestCase):
    def test_asignacion_resolucion_evolucion_recomendacion_perfil(self):
        fixtures.CierreFuncionalTests.setUp(self)
        from tests.test_citas_api import person
        admin=person('browserinstitutionadmin','ADMIN')
        password = secrets.token_urlsafe(24) + 'A9!'
        for user, first in ((self.w, 'Trabajador'), (self.p, 'Profesional'), (admin, 'Administrador')):
            user.set_password(password)
            user.first_name = first
            user.last_name = 'Sintetico'
            user.save()
        root = Path(__file__).resolve().parents[2]
        data = dict(worker=str(self.w.pk), worker_email=self.w.email, psy_email=self.p.email,
                    instrument=str(self.instrument.pk), seguimiento=str(self.seg.pk), admin_email=admin.email)
        from datetime import time, timedelta
        from django.utils import timezone
        from zoneinfo import ZoneInfo
        from src.infrastructure.persistence.django.models import DisponibilidadPsicologo, ReglaAlerta
        start = (timezone.now().astimezone(ZoneInfo('America/La_Paz')) + timedelta(days=2)).replace(hour=10, minute=0)
        data.update(inicio=start.strftime('%Y-%m-%dT%H:%M'), fin=(start + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'))
        DisponibilidadPsicologo.objects.create(psicologo=self.p, dia_semana=start.weekday(), hora_inicio=time(8), hora_fin=time(18))
        ReglaAlerta.objects.create(nombre='Regla de ensayo', rango=self.instrument.rangos.get(), nivel='MEDIA')
        run = subprocess.run(['node', str(root/'frontend/e2e/cierre-funcional.cjs')],
            env=dict(os.environ, SASPEL_TEST_API=self.live_server_url, SASPEL_TEST_PASSWORD=password,
                     SASPEL_TEST_FIXTURE=json.dumps(data)), capture_output=True, text=True,
            encoding='utf-8', timeout=180)
        self.assertEqual(run.returncode, 0, (run.stdout+run.stderr).replace(password, '[REDACTED]'))
        self.assertEqual(ResultadoInstrumento.objects.filter(aplicacion__asignacion__trabajador=self.w).count(), 2)
        self.assertEqual(Recomendacion.objects.get(seguimiento=self.seg).estado, 'COMPLETADA')
        self.w.perfil_usuario.refresh_from_db()
        self.assertEqual(self.w.perfil_usuario.telefono, '59170000000')
