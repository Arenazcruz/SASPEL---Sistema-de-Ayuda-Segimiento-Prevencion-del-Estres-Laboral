from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken
from tests.test_citas_api import setup_citas, person
from src.infrastructure.persistence.django.models import Seguimiento

class SeguimientoTests(TestCase):
    def setUp(self):
        setup_citas(self);self.url=f'/api/psicologo/trabajadores/{self.w.pk}/seguimiento/';self.auth(self.p)
        self.data={'motivo':'Revisión','categoria':'Atención','observacion':'Observación privada','estado':'En seguimiento',
                   'evolucion':'Evolución registrada por profesional','plan_accion':'Plan acordado','proxima_revision':str(timezone.localdate()+timedelta(days=7))}
    def auth(self,u):self.client.credentials(HTTP_AUTHORIZATION='Bearer '+str(AccessToken.for_user(u)))
    def post(self,**kw):return self.client.post(self.url,self.data|kw,format='json')
    def test_registro_cronologico_estado_evolucion_y_auditoria(self):
        self.assertEqual(self.post().status_code,201);self.assertEqual(self.post(estado='Cerrado',evolucion='Nueva valoración').status_code,201)
        data=self.client.get(self.url).data;self.assertEqual([r['estado'] for r in data['registros']],['En seguimiento','Cerrado'])
        self.assertEqual(data['registros'][1]['evolucion'],'Nueva valoración')
        rows=list(Seguimiento.objects.all());self.assertEqual(rows[0].creado_por,str(self.p.pk));self.assertEqual(rows[0].trabajador_id,self.w.pk)
        self.assertEqual(self.client.delete(self.url).status_code,405);self.assertEqual(self.client.patch(self.url,{},format='json').status_code,405)
        self.assertEqual(Seguimiento.objects.count(),2)
    def test_privacidad_roles_y_reasignacion(self):
        self.post()
        for u in [self.w,self.other,self.foreign,person('admin','ADMIN'),person('super','SUPERADMIN')]:
            self.auth(u);self.assertIn(self.client.get(self.url).status_code,[403,404]);self.assertIn(self.post().status_code,[403,404])
        self.auth(self.p);self.link.estado='REASIGNADA';self.link.save();self.assertEqual(self.client.get(self.url).status_code,404);self.assertEqual(self.post().status_code,404)
        self.assertEqual(Seguimiento.objects.count(),1)
    def test_validacion_no_suplanta_y_no_fechas_invalidas(self):
        for changes in [{'trabajador_id':str(self.other.pk)},{'profesional_id':str(self.foreign.pk)},{'fecha':'2020-01-01'},{'observacion':' '},{'estado':'x'*101},{'proxima_revision':'2000-01-01'}]:
            self.assertEqual(self.post(**changes).status_code,400,changes)
        self.assertEqual(Seguimiento.objects.count(),0)
        self.assertEqual(self.post(proxima_revision=None).status_code,201)
    def test_sesion_perfil_primer_acceso_y_no_cache(self):
        self.assertEqual(self.client.get(self.url)['Cache-Control'],'no-store')
        self.p.debe_cambiar_password=True;self.p.save();self.assertEqual(self.post().status_code,403)
        self.p.debe_cambiar_password=False;self.p.save();self.w.perfil_usuario.deleted=True;self.w.perfil_usuario.save()
        self.assertEqual(self.client.get(self.url).status_code,404)
        self.client.credentials();self.assertEqual(self.client.get(self.url).status_code,401)
