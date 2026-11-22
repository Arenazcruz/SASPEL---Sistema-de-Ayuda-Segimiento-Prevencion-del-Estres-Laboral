"""Composición de T23; las vistas reciben casos y el núcleo solo conoce el puerto."""

from src.infrastructure.persistence.django.repositories.assignments import DjangoAssignmentRepository


def build_assignments(case):
    return case(DjangoAssignmentRepository())
