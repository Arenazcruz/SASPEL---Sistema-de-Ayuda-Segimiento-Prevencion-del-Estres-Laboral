from dataclasses import dataclass
from src.domain.exceptions.superadmin import AdministrationError

@dataclass(frozen=True)
class ObservacionProfesional:
    texto: str

    def __post_init__(self):
        if not self.texto.strip() or len(self.texto) > 10000:
            raise AdministrationError('La observación debe contener entre 1 y 10000 caracteres.')
