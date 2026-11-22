from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from tests.test_citas_api import person
from src.infrastructure.auth.jwt_token_provider import JWTTokenProvider


class SesionPerfilTests(TestCase):
    def setUp(self):
        self.u=person('perfilpropio','TRABAJADOR');self.client=APIClient()
        self.tokens=JWTTokenProvider.issue(self.u.pk)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+self.tokens['access'])

    def test_logout_revoca_access_y_refresh_incluso_sin_access(self):
        self.client.credentials()
        r=self.client.post('/api/auth/logout/',{'refresh':self.tokens['refresh']},format='json')
        self.assertEqual(r.status_code,204,r.data)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+self.tokens['access'])
        self.assertEqual(self.client.get('/api/auth/me/').status_code,401)
        self.assertEqual(self.client.post('/api/auth/refresh/',{'refresh':self.tokens['refresh']},format='json').status_code,401)
        nuevos=JWTTokenProvider.issue(self.u.pk)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+nuevos['access'])
        self.assertEqual(self.client.get('/api/auth/me/').status_code,200)

    def test_password_nuevo_revoca_tokens_previos(self):
        self.u.set_password('Clave-sintetica-2026!');self.u.save()
        self.assertEqual(self.client.get('/api/auth/me/').status_code,401)
        self.assertEqual(self.client.post('/api/auth/refresh/',{'refresh':self.tokens['refresh']},format='json').status_code,401)

    def test_logout_rechaza_token_ajeno_no_firmado(self):
        self.assertEqual(self.client.post('/api/auth/logout/',{'refresh':'invalido'},format='json').status_code,401)
        self.u.refresh_from_db();self.assertEqual(self.u.version_sesion,0)

    def test_perfil_propio_valida_y_no_modifica_institucion_o_rol(self):
        r=self.client.patch('/api/perfil/',{'first_name':'Ana','last_name':'Prueba','telefono':'71234567'},format='json')
        self.assertEqual(r.status_code,200,r.data);self.assertEqual(r.data['telefono'],'71234567')
        for datos in ({'role':'SUPERADMIN'},{'area_id':str(self.u.pk)},{'codigo_empleado':'OTRO'},{'first_name':'123'},{'telefono':'abc'},{'fecha_nacimiento':'2099-01-01'}):
            self.assertEqual(self.client.patch('/api/perfil/',datos,format='json').status_code,400)
        self.assertEqual(self.client.get('/api/perfil/').data['codigo_empleado'],'perfilpropio')
        self.assertTrue(self.u.groups.filter(name='TRABAJADOR').exists())

    def test_perfil_nuevo_trabajador_y_borrado(self):
        nuevo=person('perfilnuevo','NUEVO_TRABAJADOR');self.client.credentials(HTTP_AUTHORIZATION='Bearer '+str(AccessToken.for_user(nuevo)))
        self.assertEqual(self.client.get('/api/perfil/').status_code,200)
        perfil=nuevo.perfil_usuario;perfil.deleted=True;perfil.save()
        self.assertEqual(self.client.get('/api/perfil/').status_code,403)
