"""Coordina consultas y transiciones de T23 mediante puertos, sin dependencias de Django.

Todas las validaciones de elegibilidad se repiten dentro de la transacción: un
selector mostrado antes en la interfaz no autoriza por sí mismo una asignación.
"""

from src.application.dto.assignments import (
    AssignmentFilters, AssignWorkerCommand, FinishAssignmentCommand, ReassignWorkerCommand,
)
from src.application.ports.input.assignments import (
    AssignmentFinishing, AssignmentListing, PsychologistLoadListing,
    UnassignedWorkerListing, WorkerAssignment, WorkerReassignment,
)
from src.application.ports.output.assignments import AssignmentRepository
from src.domain.exceptions.superadmin import AdministrationError
from src.domain.services.professional_assignment import (
    ASSIGNMENT_STATES, closing_reason, validate_active_assignment, validate_psychologist, validate_worker,
)


class AssignmentCase:
    def __init__(self, repository: AssignmentRepository):
        self.repository = repository

    def validate_pair(self, worker_id: int, psychologist_id: int):
        if worker_id == psychologist_id:
            raise AdministrationError('Trabajador y psicólogo deben ser personas diferentes.', 'psicologo_id')
        worker = self.repository.get_person(worker_id)
        psychologist = self.repository.get_person(psychologist_id)
        validate_worker(worker.role, worker.is_active)
        validate_psychologist(psychologist.role, psychologist.is_active, psychologist.habilitado_asignaciones)


class ListAssignments(AssignmentCase, AssignmentListing):
    def execute(self, filters: AssignmentFilters):
        if filters.estado and filters.estado not in ASSIGNMENT_STATES:
            raise AdministrationError('Estado de asignación inválido.', 'estado')
        if filters.page < 1:
            raise AdministrationError('La página comienza en 1.', 'page')
        return self.repository.list_assignments(filters)


class ListUnassignedWorkers(AssignmentCase, UnassignedWorkerListing):
    def execute(self, search: str = '', page: int = 1):
        if page < 1:
            raise AdministrationError('La página comienza en 1.', 'page')
        return self.repository.unassigned_workers(search, page)


class ListPsychologistLoads(AssignmentCase, PsychologistLoadListing):
    def execute(self):
        return self.repository.psychologist_loads()


class AssignWorker(AssignmentCase, WorkerAssignment):
    def execute(self, command: AssignWorkerCommand):
        with self.repository.atomic():
            self.validate_pair(command.trabajador_id, command.psicologo_id)
            if self.repository.has_active_assignment(command.trabajador_id):
                raise AdministrationError('El trabajador ya tiene una asignación ACTIVA.', 'trabajador_id')
            return self.repository.create_assignment(command.trabajador_id, command.psicologo_id)


class FinishAssignment(AssignmentCase, AssignmentFinishing):
    def execute(self, command: FinishAssignmentCommand):
        reason = closing_reason(command.motivo_fin)
        with self.repository.atomic():
            assignment = self.repository.get_assignment(command.asignacion_id)
            validate_active_assignment(assignment.estado)
            # Se permite cerrar incluso si una cuenta fue desactivada después del alta.
            return self.repository.close_assignment(assignment.id, 'FINALIZADA', reason)


class ReassignWorker(AssignmentCase, WorkerReassignment):
    def execute(self, command: ReassignWorkerCommand):
        reason = closing_reason(command.motivo_fin)
        with self.repository.atomic():
            previous = self.repository.get_assignment(command.asignacion_id)
            validate_active_assignment(previous.estado)
            if previous.psicologo.id == command.psicologo_id:
                raise AdministrationError('Selecciona un psicólogo diferente al actual.', 'psicologo_id')
            self.validate_pair(previous.trabajador.id, command.psicologo_id)
            # Ambas escrituras comparten transacción: un fallo en el alta restaura la anterior.
            self.repository.close_assignment(previous.id, 'REASIGNADA', reason)
            return self.repository.create_assignment(previous.trabajador.id, command.psicologo_id)
