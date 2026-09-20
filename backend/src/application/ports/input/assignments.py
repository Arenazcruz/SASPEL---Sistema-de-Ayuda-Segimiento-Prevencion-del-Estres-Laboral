"""Entradas explícitas del módulo de asignación manual y consulta de carga/historial."""

from typing import Protocol
from src.application.dto.assignments import (
    AssignmentDTO, AssignmentFilters, AssignmentPage, AssignWorkerCommand,
    FinishAssignmentCommand, PsychologistLoad, ReassignWorkerCommand, WorkerPage,
)


class AssignmentListing(Protocol):
    def execute(self, filters: AssignmentFilters) -> AssignmentPage: ...


class UnassignedWorkerListing(Protocol):
    def execute(self, search: str = '', page: int = 1) -> WorkerPage: ...


class PsychologistLoadListing(Protocol):
    def execute(self) -> list[PsychologistLoad]: ...


class WorkerAssignment(Protocol):
    def execute(self, command: AssignWorkerCommand) -> AssignmentDTO: ...


class AssignmentFinishing(Protocol):
    def execute(self, command: FinishAssignmentCommand) -> AssignmentDTO: ...


class WorkerReassignment(Protocol):
    def execute(self, command: ReassignWorkerCommand) -> AssignmentDTO: ...
