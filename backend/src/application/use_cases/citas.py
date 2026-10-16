from src.application.ports.output.citas import CitasRepository
from src.domain.exceptions.resultados import AccesoResultadosDenegado, ResultadoNoDisponible
from src.domain.services.citas import transicion_cita


class GestionarCitas:
    def __init__(self, repository: CitasRepository):
        self.repository = repository

    def rol(self, actor, esperado=None):
        rol = self.repository.rol_activo(actor)
        if rol not in ('TRABAJADOR', 'PSICOLOGO') or (esperado and rol != esperado):
            raise AccesoResultadosDenegado('No tienes acceso a esta función.')
        return rol

    def listar(self, actor):
        with self.repository.atomic():
            return self.repository.listar(actor, self.rol(actor))

    def contexto(self, actor):
        with self.repository.atomic():
            self.rol(actor, 'TRABAJADOR')
            return self.repository.contexto(actor)

    def solicitar(self, actor, datos):
        with self.repository.atomic():
            self.rol(actor, 'TRABAJADOR')
            return self.repository.solicitar(actor, datos)

    def accion(self, actor, cita_id, accion, motivo=''):
        with self.repository.atomic():
            rol = self.rol(actor)
            cita = self.repository.obtener(cita_id)
            if not cita or (rol == 'TRABAJADOR' and cita['trabajador_id'] != actor) or (
                rol == 'PSICOLOGO' and (cita['psicologo_id'] != actor or not
                    self.repository.tiene_asignacion_activa(actor, cita['trabajador_id']))
            ):
                raise ResultadoNoDisponible('La cita no está disponible.')
            estado = transicion_cita(cita['estado'], accion, rol, motivo)
            if accion == 'confirmar':
                self.repository.confirmar_horario(cita)
            return self.repository.cambiar_estado(cita_id, estado, motivo.strip(), actor)

    def disponibilidad(self, actor, datos=None, bloque_id=None):
        with self.repository.atomic():
            self.rol(actor, 'PSICOLOGO')
            if bloque_id:
                self.repository.desactivar_disponibilidad(actor, bloque_id)
            elif datos is not None:
                self.repository.guardar_disponibilidad(actor, datos)
            return self.repository.disponibilidad(actor)
