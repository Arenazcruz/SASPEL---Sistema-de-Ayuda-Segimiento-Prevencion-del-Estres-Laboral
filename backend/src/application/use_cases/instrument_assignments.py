from src.application.ports.output.instrument_assignments import InstrumentAssignmentsRepository
from src.domain.exceptions.resultados import AccesoResultadosDenegado, ResultadoNoDisponible
from src.domain.exceptions.superadmin import AdministrationError


class GestionarAsignacionesInstrumento:
    def __init__(self, repository: InstrumentAssignmentsRepository):
        self.repository = repository

    def ejecutar(self, actor, trabajador=None, datos=None):
        with self.repository.atomic():
            rol = self.repository.rol_activo(actor)
            if trabajador is None:
                if rol != 'TRABAJADOR':
                    raise AccesoResultadosDenegado('Solo puedes consultar tus instrumentos como trabajador.')
                return {'asignaciones': self.repository.listar(actor)}
            if rol not in ('PSICOLOGO', 'SUPERADMIN'):
                raise AccesoResultadosDenegado('No puedes asignar instrumentos.')
            if (self.repository.rol_activo(trabajador) != 'TRABAJADOR' or
                (rol == 'PSICOLOGO' and not self.repository.tiene_asignacion_activa(actor, trabajador))):
                raise ResultadoNoDisponible('El trabajador no está disponible.')
            if datos is not None:
                limite = datos.get('fecha_limite')
                if limite is not None and limite <= self.repository.ahora():
                    raise AdministrationError('La fecha límite debe ser futura.')
                return self.repository.asignar(actor, trabajador, datos['instrumento_id'], limite)
            return {'asignaciones': self.repository.listar(trabajador), 'instrumentos': self.repository.catalogo()}
