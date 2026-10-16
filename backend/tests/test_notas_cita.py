from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken
from tests.test_citas_api import setup_citas, person
from src.infrastructure.persistence.django.models import Cita, NotaCita

class NotasCitaTests(TestCase):
    def setUp(self):
        setup_citas(self)
        self.cita=Cita.objects.create(trabajador=self.w,psicologo=self.p,solicitada_por=self.w,
            fecha_inicio=timezone.now()-timedelta(hours=2),fecha_fin=timezone.now()-timedelta(hours=1),estado='CONFIRMADA',motivo='Consulta')
        self.url=f'/api/citas/{self.cita.pk}/notas/'
        self.auth(self.p)
    def auth(self,u):self.client.credentials(HTTP_AUTHORIZATION='Bearer '+str(AccessToken.for_user(u)))
    def note(self,**kw):return self.client.post(self.url,{'observacion':'Observación privada'}|kw,format='json')
    def test_completar_y_registrar_con_autor_fecha_y_historial_inmutable(self):
        self.assertEqual(self.note().status_code,400)
        r=self.client.post(f'/api/citas/{self.cita.pk}/completar/',{},format='json')
        self.assertEqual(r.status_code,200,r.data);self.assertEqual(r.data['estado'],'COMPLETADA')
        r=self.note();self.assertEqual(r.status_code,201,r.data)
        n=NotaCita.objects.get();self.assertEqual(n.profesional_id,self.p.pk);self.assertEqual(n.creado_por,str(self.p.pk))
        self.assertIsNotNone(n.creado_en);self.assertEqual(self.client.get(self.url).data[0]['observacion'],'Observación privada')
        self.assertEqual(self.client.delete(self.url).status_code,405)
        self.assertEqual(self.client.patch(self.url,{'observacion':'Cambio'},format='json').status_code,405)
        self.assertEqual(self.note(observacion='Nota adicional').status_code,201);self.assertEqual(NotaCita.objects.count(),2)
        self.auth(self.w);self.assertNotIn('Observación privada',str(self.client.get('/api/citas/').data))
    def test_acceso_ajeno_roles_y_reasignacion_revocan_lectura_y_escritura(self):
        for user in [self.w,self.other,person('admin','ADMIN'),person('super','SUPERADMIN'),self.foreign]:
            self.auth(user);self.assertIn(self.client.get(self.url).status_code,[403,404]);self.assertIn(self.note().status_code,[403,404])
        self.auth(self.p);self.link.estado='FINALIZADA';self.link.save()
        self.assertEqual(self.client.get(self.url).status_code,404);self.assertEqual(self.note().status_code,404)
        self.assertEqual(NotaCita.objects.count(),0)
    def test_validaciones_cita_futura_no_realizada_contenido_y_spoof(self):
        self.cita.fecha_inicio=self.start;self.cita.fecha_fin=self.end;self.cita.save()
        self.assertEqual(self.client.post(f'/api/citas/{self.cita.pk}/completar/',{},format='json').status_code,400)
        self.assertEqual(self.note(profesional_id=str(self.foreign.pk)).status_code,400)
        self.assertEqual(self.note(observacion=' ').status_code,400)
        self.assertEqual(self.note(observacion='x'*10001).status_code,400)
        self.auth(self.w);self.assertEqual(self.client.post(f'/api/citas/{self.cita.pk}/completar/',{},format='json').status_code,400)
    def test_sesion_primer_acceso_y_no_cache(self):
        self.assertEqual(self.client.get(self.url)['Cache-Control'],'no-store')
        self.p.debe_cambiar_password=True;self.p.save();self.assertEqual(self.note().status_code,403)
        self.client.credentials();self.assertEqual(self.client.get(self.url).status_code,401)
