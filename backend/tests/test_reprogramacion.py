from datetime import timedelta
from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken
from tests.test_citas_api import setup_citas
from src.infrastructure.api.rest.views.citas import caso
from src.infrastructure.persistence.django.models import Cita, Notificacion


class ReprogramacionTests(TestCase):
    def setUp(self):
        setup_citas(self)
        self.cita = caso().solicitar(self.w.pk, dict(fecha_inicio=self.start, fecha_fin=self.end, motivo='Sintético', prioridad='MEDIA'))
        self.url = f"/api/citas/{self.cita['id']}/reprogramar/"
        self.data = dict(fecha_inicio=(self.start+timedelta(hours=2)).isoformat(), fecha_fin=(self.end+timedelta(hours=2)).isoformat(), motivo='Cambio solicitado')

    def post(self, actor, **datos):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+str(AccessToken.for_user(actor)))
        return self.client.post(self.url, self.data | datos, format='json')

    def test_conserva_origen_y_confirma_nuevo_horario(self):
        response = self.post(self.p)
        self.assertEqual(response.status_code, 201, response.data)
        old = Cita.objects.get(pk=self.cita['id'])
        self.assertEqual((old.estado, old.fecha_inicio), ('REPROGRAMADA', self.start))
        self.assertEqual(response.data['cita_origen_id'], old.pk)
        self.assertEqual(response.data['estado'], 'CONFIRMADA')
        self.assertEqual(self.post(self.p).status_code, 400)
        self.assertEqual(Cita.objects.count(), 2)
        self.assertTrue(Notificacion.objects.filter(origen_id=old.pk, destinatario=self.w, evento__endswith='REPROGRAMADA').exists())

    def test_permisos_y_revocacion(self):
        self.assertEqual(self.post(self.w).status_code, 403)
        self.assertEqual(self.post(self.foreign).status_code, 404)
        self.link.estado='FINALIZADA'; self.link.save()
        self.assertEqual(self.post(self.p).status_code, 404)
        self.assertEqual(Cita.objects.count(), 1)

    def test_rechaza_solapamiento_sin_cerrar_original(self):
        Cita.objects.create(trabajador=self.other, psicologo=self.p, solicitada_por=self.other, fecha_inicio=self.start+timedelta(hours=2), fecha_fin=self.end+timedelta(hours=2), motivo='Sintético', estado='CONFIRMADA')
        self.assertEqual(self.post(self.p).status_code, 400)
        self.assertEqual(Cita.objects.get(pk=self.cita['id']).estado, 'SOLICITADA')

    def test_validaciones(self):
        for datos in [dict(motivo=''), dict(trabajador_id=str(self.other.pk)), dict(fecha_fin=self.start.isoformat()), dict(fecha_inicio=self.start.isoformat(), fecha_fin=self.end.isoformat())]:
            self.assertEqual(self.post(self.p, **datos).status_code, 400)
        self.assertEqual(Cita.objects.count(), 1)
