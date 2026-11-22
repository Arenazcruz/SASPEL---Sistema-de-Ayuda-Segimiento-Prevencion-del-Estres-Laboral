from src.application.ports.output.seguimiento import SeguimientoRepository
from src.domain.entities.seguimiento import DatosSeguimiento
from src.domain.exceptions.resultados import AccesoResultadosDenegado, ResultadoNoDisponible

class GestionarSeguimiento:
    def __init__(self, repository: SeguimientoRepository):
        self.repository = repository

    def ejecutar(self, actor, trabajador, datos: DatosSeguimiento | None = None):
        with self.repository.atomic():
            if self.repository.rol_activo(actor) != 'PSICOLOGO':
                raise AccesoResultadosDenegado('Solo un profesional autorizado puede acceder al seguimiento.')
            if not self.repository.tiene_asignacion_activa(actor, trabajador):
                raise ResultadoNoDisponible('El trabajador no está disponible.')
            if datos is not None:
                datos.validar(self.repository.hoy())
                return self.repository.registrar(actor, trabajador, datos)
            return self.repository.historial(trabajador)
