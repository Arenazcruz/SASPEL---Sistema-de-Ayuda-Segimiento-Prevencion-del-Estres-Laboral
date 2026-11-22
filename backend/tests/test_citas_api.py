from datetime import timedelta, time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connections, close_old_connections
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from src.infrastructure.api.rest.views.citas import caso
from src.infrastructure.persistence.django.models import Cita, DisponibilidadPsicologo, AsignacionProfesional, PerfilUsuario
from src.domain.exceptions.superadmin import AdministrationError


def person(name,role):
    u=get_user_model().objects.create_user(username=name+'@saspel.com',email=name+'@saspel.com',first_name=name)
    u.groups.add(Group.objects.get_or_create(name=role)[0])
    PerfilUsuario.objects.create(usuario=u,codigo_empleado=name,habilitado_asignaciones=role=='PSICOLOGO')
    return u


def setup_citas(test):
    Group.objects.get_or_create(name='SUPERADMIN')
    test.w=person('worker','TRABAJADOR');test.other=person('other','TRABAJADOR')
    test.p=person('psy','PSICOLOGO');test.foreign=person('foreign','PSICOLOGO')
    test.link=AsignacionProfesional.objects.create(trabajador=test.w,psicologo=test.p)
    AsignacionProfesional.objects.create(trabajador=test.other,psicologo=test.p)
    test.start=(timezone.localtime()+timedelta(days=2)).replace(hour=10,minute=0,second=0,microsecond=0)
    test.end=test.start+timedelta(hours=1)
    test.block=DisponibilidadPsicologo.objects.create(psicologo=test.p,dia_semana=test.start.weekday(),hora_inicio=time(8),hora_fin=time(18))
    test.client=APIClient()


class CitasTests(TestCase):
    def setUp(self):setup_citas(self)
    def auth(self,user):self.client.credentials(HTTP_AUTHORIZATION='Bearer '+str(AccessToken.for_user(user)))
    def request_cita(self,worker=None,**changes):
        self.auth(worker or self.w)
        data={'fecha_inicio':self.start.isoformat(),'fecha_fin':self.end.isoformat(),'motivo':'Orientación','prioridad':'MEDIA'}|changes
        return self.client.post('/api/citas/',data,format='json')
    def action(self,id,action,reason='Motivo'):
        return self.client.post(f'/api/citas/{id}/{action}/',{'motivo':reason},format='json')
    def test_flujo_solicitar_confirmar_cancelar_con_historial_y_auditoria(self):
        r=self.request_cita();self.assertEqual(r.status_code,201,r.data);id=r.data['id']
        self.assertEqual(self.client.get('/api/citas/').data[0]['estado'],'SOLICITADA')
        self.auth(self.p);self.assertEqual(self.action(id,'confirmar').data['estado'],'CONFIRMADA')
        self.auth(self.w);self.assertEqual(self.action(id,'cancelar').data['estado'],'CANCELADA')
        row=Cita.objects.get(pk=id);self.assertEqual(row.creado_por,str(self.w.pk));self.assertEqual(row.actualizado_por,str(self.w.pk))
        self.assertEqual(Cita.objects.count(),1);self.assertEqual(self.action(id,'cancelar').status_code,400)
    def test_rechazo_solo_profesional_y_motivo_obligatorio(self):
        id=self.request_cita().data['id'];self.assertEqual(self.action(id,'confirmar').status_code,400)
        self.auth(self.p);self.assertEqual(self.action(id,'rechazar','').status_code,400)
        self.assertEqual(self.action(id,'rechazar').data['estado'],'RECHAZADA')
    def test_permisos_ajenos_y_revocacion_por_reasignacion(self):
        id=self.request_cita().data['id'];self.auth(self.foreign)
        self.assertEqual(self.action(id,'confirmar').status_code,404);self.assertEqual(self.client.get('/api/citas/').data,[])
        self.link.estado='REASIGNADA';self.link.save();self.auth(self.p)
        self.assertEqual(self.action(id,'confirmar').status_code,404);self.assertEqual(self.client.get('/api/citas/').data,[])
        self.auth(self.other);self.assertEqual(self.action(id,'cancelar').status_code,404)
    def test_no_falsificar_propietario_rol_y_sin_asignacion(self):
        self.assertEqual(self.request_cita(trabajador_id=str(self.other.pk)).status_code,400)
        self.link.estado='FINALIZADA';self.link.save();self.assertEqual(self.request_cita().status_code,400)
        for role in ['ADMIN','SUPERADMIN','NUEVO_TRABAJADOR']:
            self.auth(person(role,role));self.assertEqual(self.client.get('/api/citas/').status_code,403)
    def test_horarios_futuros_disponibilidad_duplicados_y_limites(self):
        self.assertEqual(self.request_cita(fecha_fin=self.start.isoformat()).status_code,400)
        self.assertEqual(self.request_cita(fecha_inicio=(self.start-timedelta(days=3)).isoformat()).status_code,400)
        self.assertEqual(self.request_cita(fecha_fin=self.end.replace(hour=19).isoformat()).status_code,400)
        self.assertEqual(self.request_cita().status_code,201);self.assertEqual(self.request_cita().status_code,400)
    def test_solapamiento_confirmacion_y_intervalo_adyacente(self):
        one=self.request_cita().data['id'];two=self.request_cita(self.other).data['id'];self.auth(self.p)
        self.assertEqual(self.action(one,'confirmar').status_code,200);self.assertEqual(self.action(two,'confirmar').status_code,400)
        self.assertEqual(Cita.objects.get(pk=two).estado,'SOLICITADA')
        r=self.request_cita(self.other,fecha_inicio=self.end.isoformat(),fecha_fin=(self.end+timedelta(hours=1)).isoformat())
        self.assertEqual(r.status_code,201,r.data)
    def test_disponibilidad_gestion_propia_y_revocacion(self):
        self.auth(self.p);url='/api/psicologo/disponibilidad/'
        self.assertEqual(self.client.post(url,{'dia_semana':8,'hora_inicio':'10:00','hora_fin':'11:00'},format='json').status_code,400)
        self.assertEqual(self.client.post(url,{'dia_semana':self.start.weekday(),'hora_inicio':'09:00','hora_fin':'11:00'},format='json').status_code,400)
        self.auth(self.foreign);self.assertEqual(self.client.post(f'{url}{self.block.pk}/desactivar/',{},format='json').status_code,404)
        self.auth(self.p);self.assertEqual(self.client.post(f'{url}{self.block.pk}/desactivar/',{},format='json').status_code,200)
        self.assertEqual(self.request_cita().status_code,400)
    def test_seguridad_jwt_solo_metodos_expuestos_y_privacidad(self):
        self.assertEqual(self.client.get('/api/citas/').status_code,401)
        self.auth(self.w);self.assertEqual(self.client.get('/api/citas/')['Cache-Control'],'no-store')
        self.assertEqual(self.client.delete('/api/citas/').status_code,405)
        self.w.is_active=False;self.w.save();self.assertEqual(self.client.get('/api/citas/').status_code,401)
    def test_primer_acceso_bloquea_y_no_modifica_citas(self):
        self.w.debe_cambiar_password=True;self.w.save();self.assertEqual(self.request_cita().status_code,403)
        self.assertEqual(Cita.objects.count(),0)


class CitasConcurrencyTests(TransactionTestCase):
    def setUp(self):setup_citas(self)
    def test_confirmaciones_concurrentes_solo_reservan_un_horario(self):
        ids=[caso().solicitar(w.pk,{'fecha_inicio':self.start,'fecha_fin':self.end,'motivo':'Cita','prioridad':'MEDIA'})['id'] for w in [self.w,self.other]]
        barrier=Barrier(2)
        def confirm(id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:caso().accion(self.p.pk,id,'confirmar');return 'ok'
                except AdministrationError:return 'conflicto'
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:result=list(pool.map(confirm,ids))
        self.assertCountEqual(result,['ok','conflicto'])
        self.assertEqual(Cita.objects.filter(estado='CONFIRMADA').count(),1)
