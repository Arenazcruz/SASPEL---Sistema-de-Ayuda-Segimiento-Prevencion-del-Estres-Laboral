from dataclasses import dataclass
from src.domain.exceptions.superadmin import AdministrationError

@dataclass(frozen=True)
class DatosAnimo:
    estado: str
    intensidad: str
    comentario: str = ''

    def validar(self):
        if not self.estado.strip() or not self.intensidad.strip() or len(self.estado)>100 or len(self.intensidad)>100 or len(self.comentario)>3000:
            raise AdministrationError('Indica estado e intensidad; respeta los límites del formulario.')
