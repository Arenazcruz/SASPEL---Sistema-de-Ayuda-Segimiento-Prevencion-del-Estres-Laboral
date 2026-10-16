"""T32: recorrido HTTP con JWT y PostgreSQL temporal, sin mocks de negocio."""
from datetime import timedelta
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.cache import caches
from tests.test_cierre_onboarding import CierreFixture
from src.infrastructure.persistence.django.models import AsignacionProfesional, ResultadoInstrumento


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class IntegracionNucleoTests(CierreFixture, TestCase):
    def setUp(self):
        self.prepare()
        self.professional = self.person('integracion-psy', 'PSICOLOGO')
        caches['login_attempts'].clear()
        self.addCleanup(caches['login_attempts'].clear)

    def login(self, user):
        user.set_password('Integration-Test-2026!'); user.save()
        self.client.credentials()
        r = self.client.post('/api/auth/login/', {'email':user.email,'password':'Integration-Test-2026!'}, format='json')
        self.assertEqual(r.status_code,200,r.data)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+r.data['access'])
        return r

    def journey(self):
        self.assertEqual(self.login(self.user).data['user']['role'],'NUEVO_TRABAJADOR')
        r = self.client.get('/api/nuevo-trabajador/dashboard/')
        self.assertEqual(r.status_code,200,r.data)
        self.assertEqual(self.client.get('/api/trabajador/resultados/').status_code,403)
        r = self.finish(20);self.assertEqual(r.status_code,200,r.data)
        self.assertEqual(self.client.get('/api/auth/me/').data['role'],'TRABAJADOR')
        history = self.client.get('/api/trabajador/resultados/')
        self.assertEqual(history.status_code,200,history.data)
        self.assertEqual(len(history.data),1)
        self.assertEqual(float(history.data[0]['puntaje']),20)
        result = ResultadoInstrumento.objects.get()
        self.login(self.professional)
        workers = self.client.get('/api/psicologo/trabajadores/')
        self.assertEqual(workers.status_code,200,workers.data)
        self.assertEqual(self.client.get(f'/api/psicologo/resultados/{result.pk}/').status_code,200)
        start = (timezone.localtime()+timedelta(days=3)).replace(hour=10,minute=0,second=0,microsecond=0)
        r=self.client.post('/api/psicologo/disponibilidad/', {'dia_semana':start.weekday(),'hora_inicio':'08:00','hora_fin':'18:00'}, format='json')
        self.assertEqual(r.status_code,201,r.data)
        self.login(self.user)
        self.assertTrue(self.client.get('/api/citas/contexto/').data['psicologo'])
        r=self.client.post('/api/citas/', {'fecha_inicio':start.isoformat(),'fecha_fin':(start+timedelta(hours=1)).isoformat(),'motivo':'Consulta integrada'}, format='json')
        self.assertEqual(r.status_code,201,r.data)
        cita=r.data['id'];self.login(self.professional)
        self.assertEqual(self.client.post(f'/api/citas/{cita}/confirmar/',{},format='json').status_code,200)
        return result, cita

    def test_recorrido_login_evaluacion_resultado_asignacion_cita_cancelacion(self):
        result,cita=self.journey();self.login(self.user)
        self.assertEqual(self.client.get('/api/citas/').data[0]['estado'],'CONFIRMADA')
        r=self.client.post(f'/api/citas/{cita}/cancelar/',{'motivo':'Cambio de horario'},format='json')
        self.assertEqual(r.status_code,200,r.data)
        self.assertEqual(r.data['estado'],'CANCELADA')
        self.assertEqual(self.client.get('/api/trabajador/resultados/').json()[0]['id'],str(result.pk))
        self.client.credentials();self.assertEqual(self.client.get('/api/citas/').status_code,401)

    def test_revocar_asignacion_cierra_resultados_y_citas_del_profesional(self):
        result,cita=self.journey()
        AsignacionProfesional.objects.filter(trabajador=self.user).update(estado='FINALIZADA')
        self.assertEqual(self.client.get(f'/api/psicologo/resultados/{result.pk}/').status_code,404)
        self.assertEqual(self.client.get('/api/citas/').data,[])
        self.assertEqual(self.client.post(f'/api/citas/{cita}/cancelar/',{'motivo':'Intento ajeno'},format='json').status_code,404)
        self.login(self.user)
        self.assertEqual(self.client.get('/api/trabajador/resultados/').status_code,200)
        self.assertEqual(len(self.client.get('/api/citas/').data),1)
