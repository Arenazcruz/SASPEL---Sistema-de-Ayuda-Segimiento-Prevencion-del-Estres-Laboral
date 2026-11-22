from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken
from tests.test_citas_api import setup_citas,person
from src.infrastructure.persistence.django.models import EstadoAnimo,Cita,Seguimiento

class DashboardTests(TestCase):
    def setUp(self): setup_citas(self)
    def auth(self,u): self.client.credentials(HTTP_AUTHORIZATION='Bearer '+str(AccessToken.for_user(u)))
    def data(self):
        response=self.client.get('/api/dashboard/');self.assertEqual(response.status_code,200,response.data)
        return {r['clave']:r['valor'] for r in response.data['indicadores']}
    def test_propios_reales_y_sin_autoridad_en_query(self):
        EstadoAnimo.objects.create(trabajador=self.w,estado='Privado',intensidad='Leve')
        EstadoAnimo.objects.create(trabajador=self.other,estado='Privado otro',intensidad='Alta')
        self.auth(self.w);self.assertEqual(self.data()['animo'],1);self.assertNotIn('seguimientos',self.data())
        self.assertEqual(self.client.get('/api/dashboard/?usuario_id='+str(self.other.pk)).status_code,400)
        self.assertNotIn('Privado',str(self.client.get('/api/dashboard/').data))
    def test_profesional_restringido_y_revocacion(self):
        Seguimiento.objects.create(trabajador=self.w,profesional=self.p,motivo='Privado',categoria='C',observacion='Secreta',estado='Activo',evolucion='E',plan_accion='P')
        self.auth(self.p);self.assertEqual(self.data()['seguimientos'],1);self.assertEqual(self.data()['trabajadores'],2)
        self.auth(self.foreign);self.assertEqual(self.data()['seguimientos'],0)
        self.link.estado='REASIGNADA';self.link.save();self.auth(self.p);self.assertEqual(self.data()['seguimientos'],0)
    def test_administracion_solo_indicadores_operativos(self):
        for role in ['ADMIN','SUPERADMIN']:
            self.auth(person(role,role));data=self.data();self.assertGreater(data['usuarios'],0)
            self.assertFalse(set(data)&{'resultados','seguimientos','alertas','animo','factores'})
    def test_citas_futuras_filtradas_y_sesion(self):
        Cita.objects.create(trabajador=self.w,psicologo=self.p,solicitada_por=self.w,fecha_inicio=self.start,fecha_fin=self.end,motivo='Privado',estado='CONFIRMADA')
        self.auth(self.w);self.assertEqual(self.data()['citas_proximas'],1)
        self.auth(self.other);self.assertEqual(self.data()['citas_proximas'],0)
        self.auth(person('new','NUEVO_TRABAJADOR'));self.assertEqual(self.client.get('/api/dashboard/').status_code,403)
        self.client.credentials();self.assertEqual(self.client.get('/api/dashboard/').status_code,401)
