from dataclasses import dataclass
from uuid import UUID
from src.domain.exceptions.superadmin import AdministrationError

@dataclass(frozen=True)
class DatosFactor:
    tipo_id: UUID
    nivel: str
    descripcion: str

    def validar(self):
        if not self.nivel.strip() or len(self.nivel)>100 or not self.descripcion.strip() or len(self.descripcion)>3000:
            raise AdministrationError('Indica nivel y descripción dentro de los límites permitidos.')
