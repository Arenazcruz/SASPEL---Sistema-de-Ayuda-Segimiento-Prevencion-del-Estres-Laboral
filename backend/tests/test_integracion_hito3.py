"""Recorrido H3 con HTTP, JWT y PostgreSQL temporal; solo el reloj de la cita se controla."""
from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase,override_settings
from tests.test_cierre_onboarding import CierreFixture
from tests import test_integracion_nucleo as nucleo
from src.infrastructure.persistence.django.models import RangoInterpretacion,Cita,AsignacionProfesional,Alerta,Notificacion

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class IntegracionHito3Tests(CierreFixture,TestCase):
    setUp=nucleo.IntegracionNucleoTests.setUp
    login=nucleo.IntegracionNucleoTests.login
    journey=nucleo.IntegracionNucleoTests.journey

    def test_recorrido_h3_eventos_atencion_bienestar_reportes_y_revocacion(self):
        admin=self.person('h3-admin','ADMIN');self.login(admin)
        rango=RangoInterpretacion.objects.get(instrumento=self.instrument,puntaje_minimo__lte=20,puntaje_maximo__gte=20)
        r=self.client.post('/api/alertas/reglas/',{'nombre':'Regla temporal de demostración','rango_id':str(rango.pk),'nivel':'MEDIA'},format='json');self.assertEqual(r.status_code,201,r.data)
        result,cita=self.journey()
        alerts=self.client.get('/api/alertas/');self.assertEqual(alerts.status_code,200,alerts.data);self.assertEqual(len(alerts.data),1)
        alert=alerts.data[0];self.assertEqual(alert['resultado_id'],result.pk)
        notifications=self.client.get('/api/notificaciones/').data
        notification=next(n for n in notifications if n['tipo']=='ALERTA')
        self.assertEqual(self.client.post(f"/api/notificaciones/{notification['id']}/leer/",{},format='json').status_code,200)
        for state in ['EN_ATENCION','CERRADA']:
            self.assertEqual(self.client.post(f"/api/alertas/{alert['id']}/acciones/",{'estado':state,'observacion':'Acción temporal registrada'},format='json').status_code,200)
        self.assertEqual(Alerta.objects.get().acciones.count(),2)
        row=Cita.objects.get(pk=cita)
        with patch('django.utils.timezone.now',return_value=row.fecha_fin+timedelta(minutes=1)):
            r=self.client.post(f'/api/citas/{cita}/completar/',{},format='json');self.assertEqual(r.status_code,200,r.data)
        self.assertEqual(self.client.post(f'/api/citas/{cita}/notas/',{'observacion':'NOTA PRIVADA H3'},format='json').status_code,201)
        tracking=f'/api/psicologo/trabajadores/{self.user.pk}/seguimiento/'
        data={'motivo':'Revisión','categoria':'Prueba','observacion':'OBSERVACION PRIVADA H3','estado':'En seguimiento','evolucion':'Temporal','plan_accion':'Plan temporal'}
        r=self.client.post(tracking,data,format='json');self.assertEqual(r.status_code,201,r.data)
        self.assertEqual(self.client.get('/api/reportes/seguimiento/').data['total'],1)
        self.assertEqual(self.client.get('/api/reportes/seguimiento/?formato=csv').status_code,200)
        self.login(admin)
        r=self.client.post('/api/catalogos/factores/',{'nombre':'Tipo temporal H3','descripcion':'Solo pruebas'},format='json');self.assertEqual(r.status_code,201,r.data)
        # El catálogo devuelve la lista vigente tras crear.
        from src.infrastructure.persistence.django.models import TipoFactorPsicosocial
        tipo=TipoFactorPsicosocial.objects.get(nombre='Tipo temporal H3')
        for report in ['usuarios','instrumentos','citas','seguimiento']:
            r=self.client.get('/api/reportes/'+report+'/');self.assertEqual(r.status_code,200,r.data)
            self.assertNotIn('PRIVADA H3',str(r.data))
        self.assertEqual(self.client.get(tracking).status_code,403)
        self.assertEqual(self.client.get(f'/api/citas/{cita}/notas/').status_code,403)
        self.login(self.user)
        self.assertEqual(self.client.post('/api/trabajador/animo/',{'estado':'Sereno','intensidad':'Leve','comentario':'Temporal'},format='json').status_code,201)
        r=self.client.post('/api/trabajador/factores/',{'tipo_id':str(tipo.pk),'nivel':'Leve','descripcion':'Temporal'},format='json');self.assertEqual(r.status_code,201,r.data)
        cards={c['clave']:c['valor'] for c in self.client.get('/api/dashboard/').data['indicadores']}
        self.assertEqual(cards['resultados'],1);self.assertEqual(cards['animo'],1);self.assertEqual(cards['factores'],1)
        self.assertEqual(self.client.get('/api/alertas/').status_code,403)
        self.assertEqual(self.client.get('/api/reportes/seguimiento/').status_code,403)
        self.assertTrue(any(n['tipo']=='RESULTADO' for n in self.client.get('/api/notificaciones/').data))
        self.login(self.professional)
        for part in ['animo','factores','seguimiento']:
            self.assertEqual(self.client.get(f'/api/psicologo/trabajadores/{self.user.pk}/{part}/').status_code,200)
        AsignacionProfesional.objects.filter(trabajador=self.user).update(estado='FINALIZADA')
        self.assertEqual(self.client.get('/api/alertas/').data,[])
        self.assertEqual(self.client.post(f"/api/notificaciones/{notification['id']}/leer/",{},format='json').status_code,404)
        self.assertEqual(self.client.get('/api/reportes/seguimiento/').data['total'],0)
        self.assertEqual(self.client.get(tracking).status_code,404)
        self.assertEqual(self.client.get(f'/api/citas/{cita}/notas/').status_code,404)
