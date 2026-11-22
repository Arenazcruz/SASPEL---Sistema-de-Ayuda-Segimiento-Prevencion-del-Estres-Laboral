"""Alcance confirmado: una institución; Admin gestiona personal, no administradores."""
from src.domain.exceptions.superadmin import AdministrationError

PERSONNEL_ROLES = ('NUEVO_TRABAJADOR', 'TRABAJADOR', 'PSICOLOGO')


def validate_institutional_creation(role):
    if role not in ('NUEVO_TRABAJADOR', 'PSICOLOGO'):
        raise AdministrationError('Admin solo registra nuevos trabajadores y psicólogos.', 'role')
