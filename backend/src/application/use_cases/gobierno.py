from src.application.ports.output.gobierno import GobiernoRepository
from src.domain.exceptions.resultados import AccesoResultadosDenegado
from src.domain.exceptions.superadmin import AdministrationError


class GobiernoSistema:
    def __init__(self, repository: GobiernoRepository):
        self.repository = repository

    def politicas(self, actor, datos=None):
        with self.repository.atomic():
            if self.repository.rol_activo(actor) != 'SUPERADMIN':
                raise AccesoResultadosDenegado('Solo Superadmin puede publicar políticas.')
            if datos is not None:
                return self.repository.publicar(actor, datos)
            return self.repository.politicas()

    def auditoria(self, actor, filtros):
        with self.repository.atomic():
            rol = self.repository.rol_activo(actor)
            if rol not in ('SUPERADMIN', 'ADMIN'):
                raise AccesoResultadosDenegado('No tienes acceso a auditoría.')
            if filtros.get('desde') and filtros.get('hasta') and filtros['desde'] > filtros['hasta']:
                raise AdministrationError('Revisa el orden de las fechas.')
            return self.repository.auditoria(actor, rol, filtros)
