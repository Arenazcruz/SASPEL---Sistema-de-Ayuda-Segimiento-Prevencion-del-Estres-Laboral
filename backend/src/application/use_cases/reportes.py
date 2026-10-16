from src.application.ports.output.reportes import ReportesRepository
from src.domain.exceptions.resultados import AccesoResultadosDenegado
from src.domain.exceptions.superadmin import AdministrationError

class ConsultarReportes:
    def __init__(self,repository:ReportesRepository): self.repository=repository
    def ejecutar(self,actor,tipo,filtros,exportar=False):
        with self.repository.atomic():
            rol=self.repository.rol_activo(actor)
            if rol not in ('ADMIN','SUPERADMIN','PSICOLOGO'):
                raise AccesoResultadosDenegado('El rol no permite reportes operativos.')
            if tipo not in ('usuarios','instrumentos','citas','seguimiento','catalogos'):
                raise AdministrationError('Reporte no disponible.')
            if filtros.get('desde') and filtros.get('hasta') and filtros['desde']>filtros['hasta']:
                raise AdministrationError('La fecha inicial no puede superar la final.')
            if filtros.get('instrumento') and tipo!='instrumentos':
                raise AdministrationError('El filtro instrumento corresponde al reporte de instrumentos.')
            if filtros.get('area') and tipo=='instrumentos':
                raise AdministrationError('El catálogo de instrumentos no se filtra por área.')
            if rol in ('ADMIN','SUPERADMIN') and tipo=='seguimiento' and filtros.get('estado'):
                raise AdministrationError('El reporte agregado de seguimiento no admite filtros clínicos.')
            return self.repository.consultar(actor,rol,tipo,filtros,exportar)
