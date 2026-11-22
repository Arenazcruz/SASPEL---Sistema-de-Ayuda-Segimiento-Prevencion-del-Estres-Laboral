from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken
from tests.test_citas_api import setup_citas, person
from src.infrastructure.persistence.django.models import EstadoAnimo

class AnimoTests(TestCase):
    def setUp(self):
        setup_citas(self);self.url='/api/trabajador/animo/';self.pro=f'/api/psicologo/trabajadores/{self.w.pk}/animo/';self.auth(self.w)
    def auth(self,u):self.client.credentials(HTTP_AUTHORIZATION='Bearer '+str(AccessToken.for_user(u)))
    def post(self,**kw):return self.client.post(self.url,{'estado':'Tranquilo','intensidad':'Leve','comentario':'Registro personal'}|kw,format='json')
    def test_registro_propio_cronologico_y_consulta_profesional(self):
        self.assertEqual(self.post().status_code,201);self.assertEqual(self.post(estado='Animado').status_code,201)
        self.assertEqual([r['estado'] for r in self.client.get(self.url).data['registros']],['Tranquilo','Animado'])
        row=EstadoAnimo.objects.first();self.assertEqual(row.trabajador_id,self.w.pk);self.assertEqual(row.creado_por,str(self.w.pk))
        self.auth(self.p);self.assertEqual(len(self.client.get(self.pro).data['registros']),2)
        self.assertEqual(self.client.post(self.pro,{'estado':'Otro'},format='json').status_code,405)
        self.auth(self.other);self.assertEqual(self.client.get(self.url).data['registros'],[])
    def test_privacidad_roles_y_reasignacion(self):
        self.post()
        for u in [self.foreign,person('admin','ADMIN'),person('super','SUPERADMIN'),self.other]:
            self.auth(u);self.assertIn(self.client.get(self.pro).status_code,[403,404])
        self.auth(self.p);self.assertEqual(self.post().status_code,403)
        self.link.estado='FINALIZADA';self.link.save();self.assertEqual(self.client.get(self.pro).status_code,404)
        self.auth(self.w);self.assertEqual(len(self.client.get(self.url).data['registros']),1)
    def test_validaciones_sin_suplantacion_ni_borrado(self):
        for kw in [{'trabajador_id':str(self.other.pk)},{'fecha':'2000-01-01'},{'estado':' '},{'intensidad':'x'*101},{'comentario':'x'*3001}]:
            self.assertEqual(self.post(**kw).status_code,400)
        self.assertEqual(EstadoAnimo.objects.count(),0)
        self.assertEqual(self.client.delete(self.url).status_code,405)
        self.assertEqual(self.client.patch(self.url,{},format='json').status_code,405)
    def test_sesion_primer_acceso_y_perfil_inactivo(self):
        self.assertEqual(self.client.get(self.url)['Cache-Control'],'no-store')
        self.w.debe_cambiar_password=True;self.w.save();self.assertEqual(self.post().status_code,403)
        self.w.debe_cambiar_password=False;self.w.save();self.w.perfil_usuario.deleted=True;self.w.perfil_usuario.save()
        self.assertEqual(self.client.get(self.url).status_code,403)
        self.client.credentials();self.assertEqual(self.client.get(self.url).status_code,401)
