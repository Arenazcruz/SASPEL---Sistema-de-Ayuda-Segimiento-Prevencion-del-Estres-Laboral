from dataclasses import dataclass
from datetime import date
from src.domain.exceptions.superadmin import AdministrationError

@dataclass(frozen=True)
class DatosSeguimiento:
    motivo: str
    categoria: str
    observacion: str
    estado: str
    evolucion: str
    plan_accion: str
    proxima_revision: date | None = None

    def validar(self, hoy: date):
        for campo, limite in [('motivo',500),('categoria',100),('observacion',10000),('estado',100),('evolucion',5000),('plan_accion',5000)]:
            texto = getattr(self, campo)
            if not texto.strip() or len(texto) > limite:
                raise AdministrationError('Completa los datos del seguimiento dentro del límite permitido.')
        if self.proxima_revision and self.proxima_revision < hoy:
            raise AdministrationError('La próxima revisión no puede estar en el pasado.')
