from src.application.ports.output.alertas import AlertasRepository
from src.domain.exceptions.resultados import AccesoResultadosDenegado

class GestionarAlertas:
    def __init__(self, repository: AlertasRepository):
        self.repository = repository

    def generar(self, resultado):
        with self.repository.atomic():
            return self.repository.generar(resultado)

    def reglas(self, actor, datos=None, regla=None):
        with self.repository.atomic():
            if self.repository.rol_activo(actor) not in ('ADMIN','SUPERADMIN'):
                raise AccesoResultadosDenegado('Solo Administración configura reglas.')
            return self.repository.reglas(actor, datos, regla)

    def consultar(self, actor, alerta=None, datos=None):
        with self.repository.atomic():
            if self.repository.rol_activo(actor) != 'PSICOLOGO':
                raise AccesoResultadosDenegado('Solo el profesional asignado accede a alertas.')
            if alerta is not None:
                return self.repository.actuar(actor, alerta, datos)
            return self.repository.listar_alertas(actor)
