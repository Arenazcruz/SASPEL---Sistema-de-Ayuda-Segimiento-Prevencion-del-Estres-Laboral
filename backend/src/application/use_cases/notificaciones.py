from src.application.ports.output.notificaciones import NotificacionesRepository
from src.domain.exceptions.resultados import AccesoResultadosDenegado

class ConsultarNotificaciones:
    def __init__(self, repository: NotificacionesRepository): self.repository=repository
    def ejecutar(self, actor, notificacion=None, solo_pendientes=False):
        with self.repository.atomic():
            if self.repository.rol_activo(actor) not in ('TRABAJADOR','NUEVO_TRABAJADOR','PSICOLOGO','ADMIN','SUPERADMIN'):
                raise AccesoResultadosDenegado('Cuenta no disponible.')
            return self.repository.consultar(actor,notificacion,solo_pendientes)
