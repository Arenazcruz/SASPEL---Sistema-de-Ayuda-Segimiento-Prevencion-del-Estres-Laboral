from src.application.ports.output.notas_cita import NotasCitaRepository
from src.domain.entities.nota_cita import ObservacionProfesional
from src.domain.exceptions.resultados import AccesoResultadosDenegado, ResultadoNoDisponible
from src.domain.exceptions.superadmin import AdministrationError

class GestionarNotasCita:
    def __init__(self, repository: NotasCitaRepository):
        self.repository = repository

    def ejecutar(self, actor, cita_id, observacion=None):
        with self.repository.atomic():
            if self.repository.rol_activo(actor) != 'PSICOLOGO':
                raise AccesoResultadosDenegado('Solo el profesional autorizado puede consultar notas.')
            cita = self.repository.obtener(cita_id)
            if not cita or cita['psicologo_id'] != actor or not self.repository.tiene_asignacion_activa(actor, cita['trabajador_id']):
                raise ResultadoNoDisponible('La cita no está disponible.')
            if observacion is not None:
                if cita['estado'] != 'COMPLETADA':
                    raise AdministrationError('La cita debe estar completada para registrar una nota.')
                nota = ObservacionProfesional(observacion)
                return self.repository.crear_nota(actor, cita_id, nota.texto.strip())
            return self.repository.listar_notas(cita_id)
