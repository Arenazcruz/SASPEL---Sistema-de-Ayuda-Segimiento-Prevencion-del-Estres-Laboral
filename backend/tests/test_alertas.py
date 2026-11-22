from django.test import TestCase
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken
from tests.test_citas_api import setup_citas, person
from src.infrastructure.persistence.django.models import (InstrumentoPsicologico,RangoInterpretacion,AsignacionInstrumento,AplicacionInstrumento,ResultadoInstrumento,ReglaAlerta,Alerta,AccionAlerta)
from src.application.use_cases.alertas import GestionarAlertas
from src.infrastructure.persistence.django.repositories.alertas import DjangoAlertasRepository

class AlertasTests(TestCase):
    def setUp(self):
        setup_citas(self)
        self.admin=person('admin','ADMIN')
        self.instrument=InstrumentoPsicologico.objects.create(codigo='ALT',nombre='Prueba configurable')
        self.range=RangoInterpretacion.objects.create(instrumento=self.instrument,nombre='Rango elegido por institución',orden=1,puntaje_minimo=0,puntaje_maximo=100)
        self.rule=ReglaAlerta.objects.create(nombre='Regla de prueba',rango=self.range,nivel='MEDIA')
    def auth(self,user): self.client.credentials(HTTP_AUTHORIZATION='Bearer '+str(AccessToken.for_user(user)))
    def result(self,worker=None,rango=True,final=True):
        assignment=AsignacionInstrumento.objects.create(trabajador=worker or self.w,instrumento=self.instrument,origen='SISTEMA',estado='COMPLETADA')
        app=AplicacionInstrumento.objects.create(asignacion=assignment,estado='FINALIZADA' if final else 'INICIADA')
        return ResultadoInstrumento.objects.create(aplicacion=app,puntaje_total=1,rango=self.range if rango else None,fecha_calculo=timezone.now())
    def test_evento_regla_configurada_y_reintento_no_duplica(self):
        result=self.result();self.assertEqual(Alerta.objects.count(),1)
        for _ in range(3): GestionarAlertas(DjangoAlertasRepository()).generar(result.pk)
        row=Alerta.objects.get();self.assertEqual(row.resultado_id,result.pk);self.assertEqual(row.regla_id,self.rule.pk)
        self.assertEqual(row.estado,'ABIERTA');self.assertEqual(row.creado_por,'SYSTEM')
        self.rule.activa=False;self.rule.save();self.result();self.assertEqual(Alerta.objects.count(),1)
    def test_sin_rango_o_resultado_no_final_no_genera(self):
        self.result(rango=False);row=self.result(final=False);self.assertEqual(Alerta.objects.count(),0)
        row.aplicacion.estado='FINALIZADA';row.aplicacion.save();self.assertEqual(Alerta.objects.count(),1)
    def test_privacidad_y_revocacion(self):
        self.result();self.auth(self.p);data=self.client.get('/api/alertas/').data
        self.assertEqual(len(data),1);pk=data[0]['id'];self.assertEqual(data[0]['trabajador_id'],self.w.pk)
        for user in [self.w,self.admin,person('super','SUPERADMIN')]:
            self.auth(user);self.assertEqual(self.client.get('/api/alertas/').status_code,403)
        self.auth(self.foreign);self.assertEqual(self.client.get('/api/alertas/').data,[])
        self.assertEqual(self.client.post(f'/api/alertas/{pk}/acciones/',{'estado':'CERRADA','observacion':'No autorizado'},format='json').status_code,404)
        self.link.estado='REASIGNADA';self.link.save();self.auth(self.p);self.assertEqual(self.client.get('/api/alertas/').data,[])
    def test_acciones_auditables_cierre_y_campos_estrictos(self):
        self.result();pk=Alerta.objects.get().pk;url=f'/api/alertas/{pk}/acciones/';self.auth(self.p)
        self.assertEqual(self.client.post(url,{'estado':'EN_ATENCION','observacion':'Revisión'},format='json').status_code,200)
        self.assertEqual(self.client.post(url,{'estado':'CERRADA','observacion':'Acción final'},format='json').status_code,200)
        self.assertEqual(self.client.post(url,{'estado':'EN_ATENCION','observacion':'Reabrir'},format='json').status_code,400)
        self.assertEqual(self.client.post(url,{'estado':'CERRADA','observacion':'','usuario_id':str(self.admin.pk)},format='json').status_code,400)
        self.assertEqual(AccionAlerta.objects.count(),2);self.assertTrue(all(r.creado_por==str(self.p.pk) for r in AccionAlerta.objects.all()))
        self.assertEqual(self.client.get('/api/alertas/')['Cache-Control'],'no-store')
    def test_reglas_inmutables_configuracion_administrativa(self):
        self.auth(self.w);self.assertEqual(self.client.get('/api/alertas/reglas/').status_code,403)
        self.auth(self.admin);data={'nombre':'Nueva regla','rango_id':str(self.range.pk),'nivel':'ALTA'}
        self.assertEqual(self.client.post('/api/alertas/reglas/',data,format='json').status_code,400)
        self.assertEqual(self.client.post(f'/api/alertas/reglas/{self.rule.pk}/desactivar/',{},format='json').status_code,200)
        self.assertEqual(self.client.post('/api/alertas/reglas/',data,format='json').status_code,201)
        self.assertEqual(self.client.patch('/api/alertas/reglas/',data,format='json').status_code,405)
        self.rule.refresh_from_db();self.assertEqual(self.rule.nivel,'MEDIA')
    def test_jwt_primer_acceso_y_anonimo(self):
        self.assertEqual(self.client.get('/api/alertas/').status_code,401)
        self.p.debe_cambiar_password=True;self.p.save();self.auth(self.p);self.assertEqual(self.client.get('/api/alertas/').status_code,403)
