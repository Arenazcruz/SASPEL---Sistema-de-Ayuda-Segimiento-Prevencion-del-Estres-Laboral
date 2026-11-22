from django.test import TestCase
from django.db import transaction
from rest_framework_simplejwt.tokens import AccessToken
from tests.test_citas_api import setup_citas,person
from src.infrastructure.persistence.django.models import Notificacion,Cita,AsignacionInstrumento,InstrumentoPsicologico,AsignacionProfesional
from src.infrastructure.persistence.django.repositories.assignments import DjangoAssignmentRepository

class NotificacionesTests(TestCase):
    def setUp(self): setup_citas(self)
    def auth(self,user): self.client.credentials(HTTP_AUTHORIZATION='Bearer '+str(AccessToken.for_user(user)))
    def test_eventos_cita_idempotentes_y_lectura_propia(self):
        row=Cita.objects.create(trabajador=self.w,psicologo=self.p,solicitada_por=self.w,fecha_inicio=self.start,fecha_fin=self.end,motivo='Texto privado')
        row.save();self.assertEqual(Notificacion.objects.filter(tipo='CITA').count(),2)
        self.auth(self.w);data=self.client.get('/api/notificaciones/').json();item=next(n for n in data if n['tipo']=='CITA')
        self.assertNotIn('Texto privado',str(data));url=f"/api/notificaciones/{item['id']}/leer/"
        first=self.client.post(url,{},format='json');self.assertEqual(first.status_code,200)
        self.assertEqual(self.client.post(url,{},format='json').data,first.data)
        self.assertFalse(any(n['id']==item['id'] for n in self.client.get('/api/notificaciones/?pendientes=true').json()))
        self.auth(self.other);self.assertEqual(self.client.post(url,{},format='json').status_code,404)
    def test_reasignacion_retira_acceso_profesional_y_datos_falsos(self):
        self.auth(self.p);rows=self.client.get('/api/notificaciones/').json();pk=next(r['id'] for r in rows if r['origen_id']==str(self.link.pk))
        self.link.estado='REASIGNADA';self.link.save()
        self.assertEqual(self.client.post(f'/api/notificaciones/{pk}/leer/',{},format='json').status_code,404)
        self.assertEqual(self.client.get('/api/notificaciones/?destinatario_id='+str(self.w.pk)).status_code,400)
        self.assertEqual(self.client.get('/api/notificaciones/')['Cache-Control'],'no-store')
    def test_instrumentos_solo_destinatario_y_admin_sin_datos_clinicos(self):
        instrument=InstrumentoPsicologico.objects.create(codigo='NOT',nombre='Instrumento')
        row=AsignacionInstrumento.objects.create(trabajador=self.w,instrumento=instrument,origen='SISTEMA');row.save()
        self.auth(self.w);self.assertEqual(len([r for r in self.client.get('/api/notificaciones/').data if r['tipo']=='INSTRUMENTO']),1)
        self.auth(person('admin','ADMIN'));self.assertEqual(self.client.get('/api/notificaciones/').data,[])
    def test_rollback_no_deja_notificaciones_y_anonimo_bloqueado(self):
        before=Notificacion.objects.count()
        try:
            with transaction.atomic():
                Cita.objects.create(trabajador=self.w,psicologo=self.p,solicitada_por=self.w,fecha_inicio=self.start,fecha_fin=self.end,motivo='Temporal')
                raise ValueError('rollback')
        except ValueError: pass
        self.assertEqual(Notificacion.objects.count(),before)
        self.assertEqual(self.client.get('/api/notificaciones/').status_code,401)
    def test_pendiente_notifica_administracion_sin_datos_sensibles(self):
        admin=person('admin','ADMIN')
        self.link.estado='FINALIZADA';self.link.save()
        for user in [self.p,self.foreign]:
            user.perfil_usuario.habilitado_asignaciones=False;user.perfil_usuario.save()
        from src.application.use_cases.assignments import AutoAssignWorker
        case=AutoAssignWorker(DjangoAssignmentRepository());case.execute(self.w.pk);case.execute(self.w.pk)
        self.auth(admin);rows=self.client.get('/api/notificaciones/').data
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['tipo'],'ASIGNACION_PENDIENTE');self.assertNotIn(self.w.email,str(rows))
