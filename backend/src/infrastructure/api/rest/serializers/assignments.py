"""Valida transporte T23. Elegibilidad y transiciones se comprueban en el núcleo."""

from rest_framework import serializers
from src.domain.services.professional_assignment import ASSIGNMENT_STATES
from src.infrastructure.api.rest.serializers.superadmin import StrictSerializer


class WorkerFilterSerializer(StrictSerializer):
    search = serializers.CharField(required=False, allow_blank=True, max_length=200, default='')
    page = serializers.IntegerField(min_value=1, default=1)


class AssignmentFilterSerializer(WorkerFilterSerializer):
    estado = serializers.ChoiceField(choices=['', *ASSIGNMENT_STATES], required=False, default='')
    trabajador_id = serializers.IntegerField(min_value=1, required=False)
    psicologo_id = serializers.IntegerField(min_value=1, required=False)


class AssignWorkerSerializer(StrictSerializer):
    trabajador_id = serializers.IntegerField(min_value=1)
    psicologo_id = serializers.IntegerField(min_value=1)


class FinishAssignmentSerializer(StrictSerializer):
    motivo_fin = serializers.CharField(max_length=2000)


class ReassignWorkerSerializer(FinishAssignmentSerializer):
    psicologo_id = serializers.IntegerField(min_value=1)
