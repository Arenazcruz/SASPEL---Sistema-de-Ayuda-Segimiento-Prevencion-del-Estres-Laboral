from src.application.ports.output.factores import FactoresRepository
from src.domain.exceptions.resultados import AccesoResultadosDenegado, ResultadoNoDisponible

class GestionarFactores:
    def __init__(self, repository: FactoresRepository):
        self.repository = repository

    def ejecutar(self, actor, trabajador=None, datos=None):
        with self.repository.atomic():
            rol = self.repository.rol_activo(actor)
            if trabajador is None:
                if rol != 'TRABAJADOR':
                    raise AccesoResultadosDenegado('Solo el trabajador puede registrar factores propios.')
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

    def catalogo(self, actor, datos=None, tipo_id=None):
        with self.repository.atomic():
            rol = self.repository.rol_catalogo(actor)
            admin = rol in ('ADMIN','SUPERADMIN')
            if rol not in ('TRABAJADOR','PSICOLOGO','ADMIN','SUPERADMIN') or (datos is not None and not admin):
                raise AccesoResultadosDenegado('No tienes acceso a esta función.')
            if datos is not None:
                return self.repository.guardar_tipo(actor,datos,tipo_id)
            return self.repository.catalogo(admin)
