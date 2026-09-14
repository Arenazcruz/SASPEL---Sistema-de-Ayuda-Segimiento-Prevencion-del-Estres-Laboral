"""Registra persistencia en Django; conservar label api mantiene la identidad histórica."""

from django.apps import AppConfig


class PersistenceConfig(AppConfig):
    """Permite que Django encuentre los datos de SASPEL."""

    name = 'src.infrastructure.persistence.django'
    # Conserva el nombre que Django ya utiliza para reconocer estos datos.
    label = 'api'
    verbose_name = 'Persistencia SASPEL'
