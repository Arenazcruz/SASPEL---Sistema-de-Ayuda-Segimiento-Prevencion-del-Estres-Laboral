from datetime import datetime

from src.domain.exceptions.superadmin import AdministrationError


def validar_horario(inicio: datetime, fin: datetime, ahora: datetime):
    if inicio.tzinfo is None or fin.tzinfo is None or inicio <= ahora or fin <= inicio:
        raise AdministrationError('Selecciona un horario futuro con fin posterior al inicio.')


def transicion_cita(estado, accion, rol, motivo):
    reglas = {
        'completar': ('PSICOLOGO', {'CONFIRMADA'}, 'COMPLETADA'),
        'confirmar': ('PSICOLOGO', {'SOLICITADA'}, 'CONFIRMADA'),
        'rechazar': ('PSICOLOGO', {'SOLICITADA'}, 'RECHAZADA'),
        'cancelar': (None, {'SOLICITADA', 'CONFIRMADA'}, 'CANCELADA'),
    }
    regla = reglas.get(accion)
    if not regla or rol not in ('TRABAJADOR', 'PSICOLOGO') or (regla[0] and rol != regla[0]):
        raise AdministrationError('Acción no permitida.')
    if estado not in regla[1]:
        raise AdministrationError('La cita cambió de estado; actualiza el listado.')
    if accion in ('rechazar', 'cancelar') and not motivo.strip():
        raise AdministrationError('Indica el motivo del cierre.')
    return regla[2]
