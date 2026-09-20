"""API de T23; hereda JWT, SUPERADMIN, errores por campo y no-store del módulo existente."""

from dataclasses import asdict
from rest_framework.response import Response
from src.application.dto.assignments import (
    AssignmentFilters, AssignWorkerCommand, FinishAssignmentCommand, ReassignWorkerCommand,
)
from src.application.use_cases import assignments as cases
from src.infrastructure.api.rest.serializers.assignments import (
    AssignmentFilterSerializer, AssignWorkerSerializer, FinishAssignmentSerializer,
    ReassignWorkerSerializer, WorkerFilterSerializer,
)
from src.infrastructure.api.rest.views.superadmin import SuperadminView
from src.infrastructure.dependencies.assignments import build_assignments


class AssignmentsView(SuperadminView):
    def get(self, request):
        filters = AssignmentFilters(**self.validated(AssignmentFilterSerializer, request.query_params.dict()))
        return Response(asdict(build_assignments(cases.ListAssignments).execute(filters)))

    def post(self, request):
        command = AssignWorkerCommand(**self.validated(AssignWorkerSerializer, request.data))
        return Response(asdict(build_assignments(cases.AssignWorker).execute(command)), status=201)


class UnassignedWorkersView(SuperadminView):
    def get(self, request):
        filters = self.validated(WorkerFilterSerializer, request.query_params.dict())
        return Response(asdict(build_assignments(cases.ListUnassignedWorkers).execute(**filters)))


class PsychologistLoadsView(SuperadminView):
    def get(self, request):
        return Response([asdict(item) for item in build_assignments(cases.ListPsychologistLoads).execute()])


class FinishAssignmentView(SuperadminView):
    def post(self, request, assignment_id):
        command = FinishAssignmentCommand(assignment_id, **self.validated(FinishAssignmentSerializer, request.data))
        return Response(asdict(build_assignments(cases.FinishAssignment).execute(command)))


class ReassignWorkerView(SuperadminView):
    def post(self, request, assignment_id):
        command = ReassignWorkerCommand(assignment_id, **self.validated(ReassignWorkerSerializer, request.data))
        return Response(asdict(build_assignments(cases.ReassignWorker).execute(command)), status=201)
