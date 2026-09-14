"""Conecta casos administrativos con el repositorio Django; cambiar el adaptador aquí."""

from src.infrastructure.persistence.django.repositories.administration import DjangoAdministrationRepository


def build_administration(use_case):
    """Recibe clase de caso y devuelve instancia con repositorio, sin ejecutar la operación."""
    return use_case(DjangoAdministrationRepository())
