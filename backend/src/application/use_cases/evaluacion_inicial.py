from uuid import UUID

from src.application.ports.output.evaluacion_inicial import EvaluacionInicialRepository


class AsignarEvaluacionInicial:
    """Prepara una asignación pendiente sin iniciar aplicaciones ni cambiar el rol."""

    def __init__(self, repository: EvaluacionInicialRepository):
        self.repository = repository

    def execute(self, usuario_id: UUID, role: str) -> None:
        if role != 'NUEVO_TRABAJADOR':
            return
        with self.repository.atomic():
            instrumento_id = self.repository.instrumento_inicial_activo()
            if instrumento_id is not None:
                self.repository.asegurar_asignacion_inicial(usuario_id, instrumento_id)
