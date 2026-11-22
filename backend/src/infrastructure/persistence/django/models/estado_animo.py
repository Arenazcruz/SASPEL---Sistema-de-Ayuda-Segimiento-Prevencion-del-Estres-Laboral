from django.conf import settings
from django.db import models
from .auditable import AuditableModel

class EstadoAnimo(AuditableModel):
    trabajador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='estados_animo')
    estado = models.CharField(max_length=100)
    intensidad = models.CharField(max_length=100)
    comentario = models.TextField(max_length=3000, blank=True)

    class Meta:
        db_table = 'saspel_estado_animo'
        ordering = ['creado_en','id']
        indexes = [models.Index(fields=['trabajador','creado_en'], name='saspel_animo_trab_fecha_idx')]
