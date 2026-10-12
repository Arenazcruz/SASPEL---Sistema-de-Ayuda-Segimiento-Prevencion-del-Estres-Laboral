from src.application.ports.input.nuevo_trabajador import DashboardNuevoTrabajador
from src.application.use_cases.nuevo_trabajador import ConsultarDashboardNuevoTrabajador
from src.infrastructure.persistence.django.repositories.nuevo_trabajador import DjangoNuevoTrabajadorRepository


def build_dashboard_nuevo_trabajador() -> DashboardNuevoTrabajador:
    return ConsultarDashboardNuevoTrabajador(DjangoNuevoTrabajadorRepository())
