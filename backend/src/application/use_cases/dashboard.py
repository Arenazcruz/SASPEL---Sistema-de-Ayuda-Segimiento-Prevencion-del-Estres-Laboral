from src.application.ports.output.dashboard import DashboardRepository
from src.domain.exceptions.resultados import AccesoResultadosDenegado

class ConsultarDashboard:
    def __init__(self,repository:DashboardRepository): self.repository=repository
    def ejecutar(self,actor):
        with self.repository.atomic():
            rol=self.repository.rol_activo(actor)
            if rol not in ('TRABAJADOR','PSICOLOGO','ADMIN','SUPERADMIN'):
                raise AccesoResultadosDenegado('Usa el panel correspondiente a tu rol.')
            return self.repository.indicadores(actor,rol)
