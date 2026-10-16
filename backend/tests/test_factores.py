from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken
from tests.test_citas_api import setup_citas, person
from src.infrastructure.persistence.django.models import TipoFactorPsicosocial, FactorPsicosocial

class FactoresTests(TestCase):
    def setUp(self):
        setup_citas(self);self.admin=person('admin','ADMIN');self.super=person('super','SUPERADMIN')
        self.catalogo='/api/catalogos/factores/';self.url='/api/trabajador/factores/';self.pro=f'/api/psicologo/trabajadores/{self.w.pk}/factores/'
        self.tipo=TipoFactorPsicosocial.objects.create(nombre='Tipo de prueba',descripcion='Configurado por negocio');self.auth(self.w)
    def auth(self,u):self.client.credentials(HTTP_AUTHORIZATION='Bearer '+str(AccessToken.for_user(u)))
    def post(self,**kw):return self.client.post(self.url,{'tipo_id':str(self.tipo.pk),'nivel':'Moderado','descripcion':'Contexto laboral'}|kw,format='json')
    def test_cronologia_auditoria_y_nombre_historico_tras_editar_desactivar(self):
        self.assertEqual(self.post().status_code,201);self.assertEqual(self.post(nivel='Leve').status_code,201)
        self.auth(self.admin);r=self.client.put(f'{self.catalogo}{self.tipo.pk}/',{'nombre':'Nombre nuevo','descripcion':'Nueva descripción','activo':False},format='json')
        self.assertEqual(r.status_code,200,r.data);self.auth(self.w)
        history=self.client.get(self.url).data['registros'];self.assertEqual([r['nivel'] for r in history],['Moderado','Leve'])
        self.assertEqual(history[0]['tipo'],'Tipo de prueba');self.assertEqual(self.client.get(self.catalogo).data,[])
        self.assertEqual(self.post().status_code,400);self.assertEqual(FactorPsicosocial.objects.count(),2)
        row=FactorPsicosocial.objects.first();self.assertEqual(row.trabajador_id,self.w.pk);self.assertEqual(row.creado_por,str(self.w.pk))
        self.auth(self.p);self.assertEqual(len(self.client.get(self.pro).data['registros']),2)
    def test_catalogo_solo_administracion_no_da_acceso_a_registros(self):
        for user in [self.w,self.p,self.foreign]:
            self.auth(user);self.assertEqual(self.client.post(self.catalogo,{'nombre':'Ajeno'},format='json').status_code,403)
            self.assertEqual(self.client.put(f'{self.catalogo}{self.tipo.pk}/',{'nombre':'Ajeno'},format='json').status_code,403)
        for user in [self.admin,self.super]:
            self.auth(user);r=self.client.post(self.catalogo,{'nombre':user.email},format='json');self.assertEqual(r.status_code,201,r.data)
            self.assertEqual(self.client.get(self.url).status_code,403);self.assertEqual(self.client.get(self.pro).status_code,403)
        self.assertEqual(TipoFactorPsicosocial.objects.count(),3)
    def test_privacidad_propiedad_revocacion_y_sin_borrado(self):
        self.post();self.auth(self.other);self.assertEqual(self.client.get(self.url).data['registros'],[])
        self.auth(self.foreign);self.assertEqual(self.client.get(self.pro).status_code,404)
        self.auth(self.p);self.link.estado='REASIGNADA';self.link.save();self.assertEqual(self.client.get(self.pro).status_code,404)
        self.assertEqual(self.client.post(self.pro,{},format='json').status_code,405)
        self.auth(self.w);self.assertEqual(self.client.delete(self.url).status_code,405)
        self.auth(self.admin);self.assertEqual(self.client.delete(f'{self.catalogo}{self.tipo.pk}/').status_code,405)
        self.assertEqual(FactorPsicosocial.objects.count(),1)
    def test_validaciones_suplantacion_catalogo_y_sesion(self):
        for changes in [{'trabajador_id':str(self.other.pk)},{'tipo_id':'incorrecto'},{'nivel':' '},{'descripcion':'x'*3001}]:
            self.assertEqual(self.post(**changes).status_code,400)
        self.auth(self.admin);self.assertEqual(self.client.post(self.catalogo,{'nombre':'TIPO DE PRUEBA'},format='json').status_code,400)
        self.assertEqual(self.client.post(self.catalogo,{'nombre':' '},format='json').status_code,400)
        self.assertEqual(self.client.get(self.catalogo)['Cache-Control'],'no-store')
        self.auth(self.w);self.w.debe_cambiar_password=True;self.w.save();self.assertEqual(self.post().status_code,403)
        self.client.credentials();self.assertEqual(self.client.get(self.url).status_code,401)

    def test_superadmin_sin_perfil_puede_configurar_sin_acceso_clinico(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        u=get_user_model().objects.create_user(username='bootstrap@saspel.com',email='bootstrap@saspel.com',is_staff=True,is_superuser=True)
        u.groups.add(Group.objects.get(name='SUPERADMIN'));self.auth(u)
        self.assertEqual(self.client.post(self.catalogo,{'nombre':'Tipo nuevo'},format='json').status_code,201)
        self.assertEqual(self.client.get(self.pro).status_code,403)
