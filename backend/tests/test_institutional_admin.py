from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from tests.test_citas_api import person
from src.infrastructure.persistence.django.models import (
    Usuario, InstrumentoPsicologico, AsignacionProfesional, EventoAuditoria,
)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class InstitutionalAdminTests(TestCase):
    def setUp(self):
        self.admin=person('institutionadmin','ADMIN');self.sa=person('institutionroot','SUPERADMIN')
        self.worker=person('institutionworker','TRABAJADOR');self.psy=person('institutionpsy','PSICOLOGO')
        self.client=APIClient();self.auth(self.admin)
        self.base='/api/institucional/'

    def auth(self,user):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+str(AccessToken.for_user(user)))

    def payload(self,role):
        return dict(first_name='Persona',last_name='Sintetica',apellido_materno='',codigo_empleado='INSTITUCION-'+role.replace('_','-'),
                    fecha_nacimiento='1990-05-15',role=role,password='Prueba-segura-8274!',password_confirmation='Prueba-segura-8274!')

    def test_registra_solo_nuevos_y_psicologos_con_onboarding(self):
        for role in ('NUEVO_TRABAJADOR','PSICOLOGO'):
            r=self.client.post(self.base+'users/',self.payload(role),format='json')
            self.assertEqual(r.status_code,201,r.data)
            user=Usuario.objects.get(pk=r.data['id'])
            self.assertFalse(user.is_staff or user.is_superuser)
            self.assertTrue(user.debe_cambiar_password)
        count=Usuario.objects.count()
        for role in ('ADMIN','SUPERADMIN','TRABAJADOR'):
            self.assertEqual(self.client.post(self.base+'users/',self.payload(role),format='json').status_code,400)
        self.assertEqual(Usuario.objects.count(),count)

    def test_lista_resumen_y_busqueda_no_revelan_administradores(self):
        r=self.client.get(self.base+'users/')
        self.assertEqual(r.status_code,200,r.data)
        self.assertEqual({str(x['id']) for x in r.data['results']},{str(self.worker.pk),str(self.psy.pk)})
        self.assertEqual(self.client.get(self.base+'users/?role=ADMINISTRADORES').data['count'],0)
        self.assertEqual(self.client.get(self.base+'dashboard/summary/').data['admins'],0)
        self.sa.groups.add(Group.objects.get(name='PSICOLOGO'))
        self.assertEqual(self.client.get(self.base+'users/').data['count'],2)

    def test_ids_directos_no_permiten_modificar_admin_ni_escalar_rol(self):
        for user in (self.admin,self.sa):
            url=self.base+f'users/{user.pk}/'
            self.assertEqual(self.client.get(url).status_code,404)
            self.assertEqual(self.client.patch(url,{'first_name':'Alterado'},format='json').status_code,404)
            for action in ('activate','deactivate','reset-password'):
                body={'password':'Cambio-seguro-674!','password_confirmation':'Cambio-seguro-674!'} if action=='reset-password' else {}
                self.assertEqual(self.client.post(url+action+'/',body,format='json').status_code,404)
        self.assertEqual(self.client.post(self.base+f'users/{self.psy.pk}/role/',{'role':'SUPERADMIN'},format='json').status_code,404)
        self.assertEqual(self.client.patch(self.base+f'users/{self.psy.pk}/',{'is_superuser':True},format='json').status_code,400)

    def test_actualizacion_y_desactivacion_preservan_historial(self):
        link=AsignacionProfesional.objects.create(trabajador=self.worker,psicologo=self.psy)
        url=self.base+f'users/{self.worker.pk}/'
        self.assertEqual(self.client.patch(url,{'telefono':'71234567'},format='json').status_code,200)
        self.assertEqual(self.client.post(url+'deactivate/',{},format='json').status_code,200)
        self.worker.refresh_from_db();self.assertFalse(self.worker.is_active)
        self.assertTrue(AsignacionProfesional.objects.filter(pk=link.pk).exists())
        self.assertEqual(self.client.post(url+'activate/',{},format='json').status_code,200)
        self.assertTrue(EventoAuditoria.objects.filter(actor=self.admin,entidad='usuario').exists())

    def test_catalogos_instrumentos_y_contenido_comparten_validaciones(self):
        for kind in ('areas','cargos'):
            r=self.client.post(self.base+kind+'/',{'nombre':'Sintético','descripcion':'Prueba'},format='json')
            self.assertEqual(r.status_code,201,r.data)
        r=self.client.post(self.base+'instruments/',{'codigo':'INST','nombre':'Sintético','version':'1'},format='json')
        self.assertEqual(r.status_code,201,r.data);pk=r.data['id']
        r=self.client.post(self.base+f'instruments/{pk}/questions/',{'texto':'Pregunta','orden':1,'tipo_respuesta':'TEXTO','obligatoria':True},format='json')
        self.assertEqual(r.status_code,201,r.data)
        self.assertEqual(self.client.post(self.base+f'instruments/{pk}/deactivate/',{},format='json').status_code,200)
        self.assertFalse(InstrumentoPsicologico.objects.get(pk=pk).activo)

    def test_reasignacion_autorizada_preserva_origen(self):
        link=AsignacionProfesional.objects.create(trabajador=self.worker,psicologo=self.psy)
        other=person('institutionotherpsy','PSICOLOGO')
        r=self.client.post(self.base+f'assignments/{link.pk}/reassign/',{'psicologo_id':str(other.pk),'motivo_fin':'Cambio sintético'},format='json')
        self.assertEqual(r.status_code,201,r.data)
        link.refresh_from_db();self.assertEqual(link.estado,'REASIGNADA')
        self.assertEqual(AsignacionProfesional.objects.filter(trabajador=self.worker,estado='ACTIVA').count(),1)

    def test_roles_revocacion_y_superficie_clinica(self):
        for url in ('/api/superadmin/users/','/api/administracion/politicas/','/api/trabajador/evolucion/',f'/api/psicologo/trabajadores/{self.worker.pk}/seguimiento/'):
            self.assertEqual(self.client.get(url).status_code,403)
        for user in (self.worker,self.psy):
            self.auth(user);self.assertEqual(self.client.get(self.base+'users/').status_code,403)
        self.auth(self.admin);self.admin.groups.clear()
        self.assertEqual(self.client.get(self.base+'users/').status_code,403)

    def test_vinculos_area_cargo_reversibles_sin_perder_perfiles(self):
        from uuid import uuid4
        from src.infrastructure.persistence.django.models import AreaInstitucional, CargoInstitucional, AreaCargo
        area=AreaInstitucional.objects.create(nombre='Área sintética')
        cargo=CargoInstitucional.objects.create(nombre='Cargo sintético')
        profile=self.worker.perfil_usuario;profile.area=area;profile.cargo=cargo;profile.save()
        url=self.base+f'areas/{area.pk}/cargos/'
        body={'cargo_ids':[str(cargo.pk)]}
        self.assertEqual(self.client.put(url,body,format='json').status_code,200)
        original=AreaCargo.objects.get(area=area,cargo=cargo).pk
        self.assertEqual(str(self.client.get(self.base+f'cargos/?area={area.pk}').data[0]['id']),str(cargo.pk))
        self.assertEqual(self.client.put(url,{'cargo_ids':[str(uuid4())]},format='json').status_code,400)
        self.assertEqual(self.client.get(url).data,body)
        self.assertEqual(self.client.put(url,{'cargo_ids':body['cargo_ids']*2},format='json').status_code,400)
        self.assertEqual(self.client.put(url,{'cargo_ids':[]},format='json').status_code,200)
        profile.refresh_from_db();self.assertEqual(profile.area,area);self.assertEqual(profile.cargo,cargo)
        self.assertTrue(AreaCargo.objects.get(pk=original).deleted)
        self.assertEqual(self.client.put(url,body,format='json').status_code,200)
        self.assertEqual(AreaCargo.objects.get(area=area,cargo=cargo).pk,original)
        cargo.activo=False;cargo.save()
        self.assertEqual(self.client.put(url,body,format='json').status_code,400)
        self.auth(self.worker);self.assertEqual(self.client.put(url,body,format='json').status_code,403)
