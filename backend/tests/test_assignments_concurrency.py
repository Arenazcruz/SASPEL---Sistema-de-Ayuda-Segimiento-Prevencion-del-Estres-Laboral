"""Dos conexiones PostgreSQL compiten por el mismo trabajador o vínculo vigente."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.db import close_old_connections, connections
from django.test import TransactionTestCase
from src.application.dto.assignments import AssignWorkerCommand, ReassignWorkerCommand, FinishAssignmentCommand
from src.application.use_cases.assignments import AssignWorker, ReassignWorker, FinishAssignment
from src.domain.exceptions.superadmin import AdministrationError
from src.infrastructure.dependencies.assignments import build_assignments
from src.infrastructure.persistence.django.models import AsignacionProfesional
from tests.test_assignments_api import person


class AssignmentConcurrencyTests(TransactionTestCase):
    def setUp(self):
        person('root-concurrency', 'SUPERADMIN')
        self.worker = person('worker-concurrency', 'TRABAJADOR')
        self.psychologists = [person(f'psych-concurrency-{i}', 'PSICOLOGO') for i in range(3)]

    def compete(self, operations):
        """La barrera inicia las peticiones a la vez; cada hilo usa su propia conexión."""
        start = Barrier(2)

        def run(operation):
            close_old_connections()
            try:
                start.wait(timeout=10)
                case, command = operation
                try:
                    build_assignments(case).execute(command)
                    return 'ok'
                except AdministrationError:
                    return 'rejected'
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(run, operation) for operation in operations]
            return [future.result(timeout=20) for future in futures]

    def test_simultaneous_assignments_create_only_one_active(self):
        results = self.compete([(AssignWorker, AssignWorkerCommand(self.worker.pk, p.pk)) for p in self.psychologists[:2]])
        self.assertCountEqual(results, ['ok', 'rejected'])
        self.assertEqual(AsignacionProfesional.objects.count(), 1)
        self.assertEqual(AsignacionProfesional.objects.get().estado, 'ACTIVA')

    def test_simultaneous_reassignments_keep_exactly_one_new_link(self):
        previous = build_assignments(AssignWorker).execute(AssignWorkerCommand(self.worker.pk, self.psychologists[0].pk))
        results = self.compete([(ReassignWorker, ReassignWorkerCommand(previous.id, p.pk, 'Cambio')) for p in self.psychologists[1:]])
        self.assertCountEqual(results, ['ok', 'rejected'])
        self.assertEqual(AsignacionProfesional.objects.count(), 2)
        self.assertEqual(AsignacionProfesional.objects.filter(estado='ACTIVA').count(), 1)
        self.assertEqual(AsignacionProfesional.objects.get(pk=previous.id).estado, 'REASIGNADA')

    def test_finish_and_reassign_cannot_both_close_the_same_link(self):
        previous = build_assignments(AssignWorker).execute(AssignWorkerCommand(self.worker.pk, self.psychologists[0].pk))
        results = self.compete([
            (FinishAssignment, FinishAssignmentCommand(previous.id, 'Fin')),
            (ReassignWorker, ReassignWorkerCommand(previous.id, self.psychologists[1].pk, 'Cambio')),
        ])
        self.assertCountEqual(results, ['ok', 'rejected'])
        self.assertLessEqual(AsignacionProfesional.objects.filter(estado='ACTIVA').count(), 1)
        self.assertIsNotNone(AsignacionProfesional.objects.get(pk=previous.id).fecha_fin)
