from django.db import models

from .area_institucional import AreaInstitucional
from .auditable import AuditableModel
from .cargo_institucional import CargoInstitucional


class AreaCargo(AuditableModel):
    """Vincula un cargo con un área sin duplicar ninguno de los catálogos."""
    area = models.ForeignKey(AreaInstitucional, on_delete=models.PROTECT, related_name='relaciones_cargo')
    cargo = models.ForeignKey(CargoInstitucional, on_delete=models.PROTECT, related_name='relaciones_area')

    class Meta:
        db_table = 'saspel_area_cargo'
        constraints = [
            models.UniqueConstraint(fields=['area', 'cargo'], name='area_cargo_unico'),
        ]

    def __str__(self):
        return f'{self.area} / {self.cargo}'
