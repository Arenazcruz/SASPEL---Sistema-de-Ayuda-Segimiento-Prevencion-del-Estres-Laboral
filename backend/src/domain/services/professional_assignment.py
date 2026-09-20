"""Reglas de asignación manual. No resuelve tamizaje, cambio de rol ni reparto automático."""

from src.domain.exceptions.superadmin import AdministrationError

# La asignación manual no equivale a completar la evaluación inicial.
WORKER_ROLES = frozenset({'TRABAJADOR', 'NUEVO_TRABAJADOR'})
ASSIGNMENT_STATES = ('ACTIVA', 'FINALIZADA', 'REASIGNADA')


def validate_worker(role: str | None, active: bool):
    if role not in WORKER_ROLES or not active:
        raise AdministrationError('Selecciona un trabajador activo.', 'trabajador_id')


def validate_psychologist(role: str | None, active: bool, enabled: bool):
    if role != 'PSICOLOGO' or not active or not enabled:
        raise AdministrationError(
            'Selecciona un PSICOLOGO activo y habilitado para recibir asignaciones.', 'psicologo_id',
        )


def validate_active_assignment(state: str):
    if state != 'ACTIVA':
        raise AdministrationError('La asignación ya está cerrada. Actualiza el listado.', 'asignacion_id')


def closing_reason(value: str) -> str:
    """Exige un motivo administrativo breve; no debe contener notas clínicas."""
    reason = value.strip()
    if not reason or len(reason) > 2000:
        raise AdministrationError('Indica un motivo de cierre de entre 1 y 2000 caracteres.', 'motivo_fin')
    return reason
