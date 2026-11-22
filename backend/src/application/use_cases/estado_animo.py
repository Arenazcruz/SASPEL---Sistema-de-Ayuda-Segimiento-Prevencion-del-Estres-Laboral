from src.application.ports.output.estado_animo import EstadoAnimoRepository
from src.domain.entities.estado_animo import DatosAnimo
from src.domain.exceptions.resultados import AccesoResultadosDenegado, ResultadoNoDisponible

class GestionarAnimo:
    def __init__(self, repository: EstadoAnimoRepository):
        self.repository = repository

    def ejecutar(self, actor, trabajador=None, datos: DatosAnimo | None = None):
        with self.repository.atomic():
            rol = self.repository.rol_activo(actor)
            if trabajador is None:
                if rol != 'TRABAJADOR':
                    raise AccesoResultadosDenegado('Solo el trabajador puede registrar y consultar su ánimo.')
                trabajador = actor
            else:
                if rol != 'PSICOLOGO' or datos is not None:
                    raise AccesoResultadosDenegado('No tienes acceso a esta función.')
                if not self.repository.tiene_asignacion_activa(actor,trabajador):
                    raise ResultadoNoDisponible('El trabajador no está disponible.')
            if datos is not None:
                datos.validar()
                return self.repository.registrar(actor,datos)
            return self.repository.historial(trabajador)
