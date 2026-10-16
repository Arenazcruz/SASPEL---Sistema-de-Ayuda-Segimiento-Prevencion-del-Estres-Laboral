import csv,io
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken
from tests.test_citas_api import setup_citas,person
from src.infrastructure.persistence.django.models import Cita,Seguimiento,InstrumentoPsicologico,AsignacionInstrumento

class ReportesTests(TestCase):
    def setUp(self):
        setup_citas(self);self.admin=person('admin','ADMIN')
        self.cita=Cita.objects.create(trabajador=self.w,psicologo=self.p,solicitada_por=self.w,fecha_inicio=self.start,fecha_fin=self.end,motivo='SECRETO CLINICO')
        Seguimiento.objects.create(trabajador=self.w,profesional=self.p,motivo='Privado',categoria='Privada',observacion='SECRETO CLINICO',estado='Valoración privada',evolucion='Confidencial',plan_accion='Plan privado')
    def auth(self,u): self.client.credentials(HTTP_AUTHORIZATION='Bearer '+str(AccessToken.for_user(u)))
    def test_admin_agregado_no_filtra_contenido_clinico(self):
        self.auth(self.admin)
        for tipo in ['citas','seguimiento']:
            r=self.client.get('/api/reportes/'+tipo+'/');self.assertEqual(r.status_code,200,r.data);self.assertTrue(r.data['agregado'])
            self.assertNotIn(self.w.email,str(r.data));self.assertNotIn('privad',str(r.data).lower());self.assertNotIn('SECRETO',str(r.data))
            self.assertEqual(r.data['filas'][0][-1],1)
        self.assertEqual(self.client.get('/api/reportes/seguimiento/?estado=Valoración').status_code,400)
    def test_profesional_solo_asignados_y_revocacion(self):
        self.auth(self.p);r=self.client.get('/api/reportes/seguimiento/');self.assertEqual(r.status_code,200,r.data)
        self.assertEqual(r.data['filas'][0][0],self.w.email);self.assertNotIn('SECRETO',str(r.data))
        self.auth(self.foreign);self.assertEqual(self.client.get('/api/reportes/seguimiento/').data['total'],0)
        self.link.estado='REASIGNADA';self.link.save();self.auth(self.p);self.assertEqual(self.client.get('/api/reportes/citas/').data['total'],0)
        self.assertEqual(self.client.get('/api/reportes/seguimiento/?formato=csv').status_code,200)
    def test_fechas_estado_y_exportacion_equivalente(self):
        self.auth(self.p);date=str(self.start.date());params={'desde':date,'hasta':date,'estado':'SOLICITADA'}
        r=self.client.get('/api/reportes/citas/',params);self.assertEqual(r.data['total'],1)
        export=self.client.get('/api/reportes/citas/',params|{'formato':'csv'});self.assertEqual(export.status_code,200)
        parsed=list(csv.reader(io.StringIO(export.content.decode('utf-8-sig'))));self.assertEqual(parsed[0],r.data['columnas']);self.assertEqual(len(parsed),2)
        self.assertEqual(export['Cache-Control'],'no-store');self.assertIn('attachment',export['Content-Disposition'])
        self.assertEqual(self.client.get('/api/reportes/citas/',{'desde':str(self.start.date()+timedelta(days=1))}).data['total'],0)
        self.assertEqual(self.client.get('/api/reportes/citas/',{'estado':'CONFIRMADA'}).data['total'],0)
    def test_usuarios_instrumentos_y_csv_seguro(self):
        self.auth(self.admin);self.w.first_name='=HYPERLINK("test")';self.w.save()
        export=self.client.get('/api/reportes/usuarios/?formato=csv');self.assertIn("'=HYPERLINK",export.content.decode('utf-8-sig').replace('""','"'))
        a=InstrumentoPsicologico.objects.create(codigo='A',nombre='Visible');InstrumentoPsicologico.objects.create(codigo='B',nombre='Ajeno')
        AsignacionInstrumento.objects.create(trabajador=self.w,instrumento=a,origen='SISTEMA')
        self.auth(self.p);self.assertEqual(self.client.get('/api/reportes/instrumentos/').data['total'],1)
        self.assertEqual(len(self.client.get('/api/reportes/catalogos/').data['instrumentos']),1)
    def test_validaciones_y_accesos_negativos(self):
        self.auth(self.admin)
        for params in [{'desde':'mal'},{'desde':'2026-10-24','hasta':'2026-10-01'},{'pagina':'0'},{'formato':'pdf'},{'area':'bad'},{'user_id':str(self.other.pk)},{'estado':'inexistente'}]:
            self.assertEqual(self.client.get('/api/reportes/citas/',params).status_code,400,params)
        self.assertEqual(self.client.get('/api/reportes/catalogos/?formato=csv').status_code,400)
        for u in [self.w,person('new','NUEVO_TRABAJADOR')]:
            self.auth(u);self.assertEqual(self.client.get('/api/reportes/usuarios/').status_code,403)
        self.client.credentials();self.assertEqual(self.client.get('/api/reportes/usuarios/').status_code,401)
