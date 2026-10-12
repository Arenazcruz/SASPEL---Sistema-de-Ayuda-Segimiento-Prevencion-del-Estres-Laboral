from uuid import UUID

from src.application.dto.nuevo_trabajador import DashboardNuevoTrabajadorDTO, EvaluacionInicialDTO
from src.application.ports.output.nuevo_trabajador import NuevoTrabajadorRepository


class ConsultarDashboardNuevoTrabajador:
    def __init__(self, repository: NuevoTrabajadorRepository):
        self.repository = repository

    def execute(self, usuario_id: UUID) -> DashboardNuevoTrabajadorDTO:
        evaluacion = self.repository.evaluacion_inicial(usuario_id)
        return DashboardNuevoTrabajadorDTO(evaluacion or EvaluacionInicialDTO('SIN_ASIGNAR'))
