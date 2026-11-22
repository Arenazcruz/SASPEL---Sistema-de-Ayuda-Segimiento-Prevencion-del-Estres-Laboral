from src.application.ports.input.primer_acceso import PrimerAcceso
from src.application.use_cases.primer_acceso import GestionarPrimerAcceso
from src.infrastructure.persistence.django.repositories.primer_acceso import DjangoPrimerAccesoRepository


def build_primer_acceso() -> PrimerAcceso:
    return GestionarPrimerAcceso(DjangoPrimerAccesoRepository())
