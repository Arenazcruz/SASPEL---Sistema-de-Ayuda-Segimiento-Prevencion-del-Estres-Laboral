from src.application.ports.output.evolucion import EvolucionRepository
from src.domain.services.evolucion import agrupar_evolucion
from src.domain.exceptions.resultados import AccesoResultadosDenegado, ResultadoNoDisponible
from src.domain.exceptions.superadmin import AdministrationError


class ConsultarEvolucion:
    def __init__(self, repository: EvolucionRepository):
        self.repository = repository

    def ejecutar(self, actor, trabajador=None, filtros=None):
        filtros = filtros or {}
        if filtros.get('desde') and filtros.get('hasta') and filtros['desde'] > filtros['hasta']:
            raise AdministrationError('La fecha inicial debe ser anterior a la final.')
        with self.repository.atomic():
            rol = self.repository.rol_activo(actor)
            if trabajador is None:
                if rol != 'TRABAJADOR':
                    raise AccesoResultadosDenegado('Solo puedes consultar tu propia evolución como trabajador.')
                trabajador = actor
            elif rol != 'PSICOLOGO':
                raise AccesoResultadosDenegado('Solo el profesional asignado puede consultar esta evolución.')
            elif not self.repository.tiene_asignacion_activa(actor, trabajador):
                raise ResultadoNoDisponible('El trabajador no está disponible.')
            return {'series': agrupar_evolucion(self.repository.puntos(trabajador, filtros))}
