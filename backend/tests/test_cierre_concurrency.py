"""Carreras reales en PostgreSQL: la exclusión debe cubrir toda la operación."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from django.db import close_old_connections, connections
from django.test import TransactionTestCase
from tests.test_citas_api import setup_citas
from src.domain.exceptions.superadmin import AdministrationError
from src.infrastructure.api.rest.views.citas import caso
from src.application.use_cases.instrument_assignments import GestionarAsignacionesInstrumento
from src.infrastructure.persistence.django.repositories.instrument_assignments import DjangoInstrumentAssignmentsRepository
from src.infrastructure.persistence.django.models import (
    Cita, InstrumentoPsicologico, EscalaRespuesta, OpcionRespuesta,
    PreguntaInstrumento, AsignacionInstrumento,
)


class CierreConcurrencyTests(TransactionTestCase):
    def setUp(self):
        setup_citas(self)

    def competir(self, operation):
        barrier = Barrier(2)
        def run(_):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    operation()
                    return 'ok'
                except AdministrationError:
                    return 'conflicto'
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(run, range(2))), ['ok', 'conflicto'])

    def test_reprogramacion_simultanea_crea_un_sucesor(self):
        old = caso().solicitar(self.w.pk, dict(fecha_inicio=self.start, fecha_fin=self.end,
                                             motivo='Sintético', prioridad='MEDIA'))
        self.competir(lambda: caso().reprogramar(self.p.pk, old['id'], dict(
            fecha_inicio=self.start+timedelta(hours=2), fecha_fin=self.end+timedelta(hours=2), motivo='Cambio')))
        self.assertEqual(Cita.objects.filter(cita_origen_id=old['id']).count(), 1)
        self.assertEqual(Cita.objects.filter(estado='CONFIRMADA').count(), 1)

    def test_asignacion_simultanea_no_duplica_pendiente(self):
        instrument = InstrumentoPsicologico.objects.create(codigo='CONCURRENTE', nombre='Sintético')
        scale = EscalaRespuesta.objects.create(nombre='Sintética')
        OpcionRespuesta.objects.create(escala=scale, etiqueta='Opción', valor=1, orden=1)
        PreguntaInstrumento.objects.create(instrumento=instrument, escala=scale, texto='Sintético',
                                          tipo_respuesta='ESCALA', orden=1)
        self.competir(lambda: GestionarAsignacionesInstrumento(DjangoInstrumentAssignmentsRepository()).ejecutar(
            self.p.pk, self.w.pk, {'instrumento_id': instrument.pk}))
        self.assertEqual(AsignacionInstrumento.objects.filter(trabajador=self.w, instrumento=instrument).count(), 1)
