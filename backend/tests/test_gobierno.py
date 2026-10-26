from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from tests.test_citas_api import person
from src.infrastructure.persistence.django.models import EventoAuditoria, PoliticaSistema, AceptacionPolitica, EstadoAnimo


class GobiernoTests(TestCase):
    def setUp(self):
        self.sa=person('gobsa','SUPERADMIN');self.admin=person('gobadmin','ADMIN');self.w=person('gobworker','TRABAJADOR')
        self.client=APIClient()
        self.data={'tipo':'TERMINOS_USO','titulo':'Texto sintético','version':'1','contenido':'Contenido de prueba','obligatoria':True}

    def auth(self,u):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+str(AccessToken.for_user(u)))

    def test_publicacion_conserva_historia_y_exige_nueva_aceptacion(self):
        self.auth(self.sa);url='/api/administracion/politicas/'
        r=self.client.post(url,self.data,format='json');self.assertEqual(r.status_code,201,r.data)
        primera=PoliticaSistema.objects.get(pk=r.data['id'])
        AceptacionPolitica.objects.create(usuario=self.w,politica=primera)
        AceptacionPolitica.objects.create(usuario=self.sa,politica=primera)
        r=self.client.post(url,self.data|{'version':'2'},format='json');self.assertEqual(r.status_code,201,r.data)
        primera.refresh_from_db();self.assertFalse(primera.activo)
        self.assertEqual(PoliticaSistema.objects.count(),2)
        self.auth(self.w)
        self.assertEqual(self.client.get('/api/trabajador/instrumentos/').status_code,403)
        pendientes=self.client.get('/api/auth/primer-acceso/politicas/')
        self.assertEqual(pendientes.status_code,200)
        self.assertIn('2',str(pendientes.data))
        self.assertEqual(AceptacionPolitica.objects.filter(usuario=self.w).count(),1)

    def test_publicar_solo_superadmin_y_no_sobrescribe_version(self):
        url='/api/administracion/politicas/'
        for u in (self.admin,self.w):
            self.auth(u);self.assertEqual(self.client.post(url,self.data,format='json').status_code,403)
        self.auth(self.sa)
        self.client.post(url,self.data|{'obligatoria':False},format='json')
        self.assertEqual(self.client.post(url,self.data,format='json').status_code,400)
        self.assertEqual(PoliticaSistema.objects.count(),1)
        row=PoliticaSistema.objects.get();row.contenido='Cambio'
        with self.assertRaises(ValidationError):row.save()

    def test_auditoria_actor_sin_contenido_sensible_y_paginacion(self):
        self.auth(self.w)
        response=self.client.post('/api/trabajador/animo/',{'estado':'Sereno','intensidad':'Leve','comentario':'SECRETO CLINICO'},format='json')
        self.assertEqual(response.status_code,201,response.data)
        event=EventoAuditoria.objects.filter(entidad='estadoanimo',actor=self.w).latest('fecha')
        self.assertEqual(event.entidad_id,EstadoAnimo.objects.get().pk)
        self.assertEqual(event.estado,'')
        self.assertEqual(self.client.get('/api/administracion/auditoria/').status_code,403)
        self.auth(self.sa);r=self.client.get('/api/administracion/auditoria/')
        self.assertEqual(r.status_code,200);self.assertNotIn('SECRETO',str(r.data))
        self.assertEqual(self.client.get('/api/administracion/auditoria/?page=999999').data['results'],[])
        self.assertEqual(self.client.get('/api/administracion/auditoria/?page=0').status_code,400)
        self.auth(self.admin);self.assertEqual(self.client.get('/api/administracion/auditoria/').data['results'],[])

    def test_eventos_son_inmutables_y_api_solo_lectura(self):
        row=EventoAuditoria.objects.first();row.accion='CAMBIO'
        with self.assertRaises(ValidationError):row.save()
        with self.assertRaises(ValidationError):row.delete()
        self.auth(self.sa)
        self.assertEqual(self.client.delete('/api/administracion/auditoria/').status_code,405)

    def test_login_registra_actor_sin_credenciales(self):
        self.w.set_password('Clave-sintetica-2026!');self.w.save()
        response=self.client.post('/api/auth/login/',{'email':self.w.email,'password':'Clave-sintetica-2026!'},format='json')
        self.assertEqual(response.status_code,200,response.data)
        event=EventoAuditoria.objects.filter(actor=self.w,accion='POST',entidad='api/auth/login/').get()
        self.assertIsNone(event.entidad_id)
        self.assertNotIn('Clave',str(event.__dict__))
