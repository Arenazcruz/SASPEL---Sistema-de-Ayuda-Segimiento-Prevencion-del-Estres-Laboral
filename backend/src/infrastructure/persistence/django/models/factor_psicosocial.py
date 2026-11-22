from django.conf import settings
from django.db import models
from .auditable import AuditableModel

class TipoFactorPsicosocial(AuditableModel):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(max_length=1000, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'saspel_tipo_factor_psicosocial'
        ordering = ['nombre','id']

class FactorPsicosocial(AuditableModel):
    trabajador = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='factores_psicosociales')
    tipo = models.ForeignKey(TipoFactorPsicosocial,on_delete=models.PROTECT,related_name='registros')
    # Conserva el nombre con el que el trabajador registró el factor.
    tipo_nombre = models.CharField(max_length=120)
    nivel = models.CharField(max_length=100)
    descripcion = models.TextField(max_length=3000)

    class Meta:
        db_table = 'saspel_factor_psicosocial'
        ordering = ['creado_en','id']
        indexes = [models.Index(fields=['trabajador','creado_en'],name='saspel_factor_trab_fecha_idx')]
