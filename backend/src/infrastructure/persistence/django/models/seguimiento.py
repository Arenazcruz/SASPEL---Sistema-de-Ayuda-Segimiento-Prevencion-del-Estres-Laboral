from django.conf import settings
from django.db import models
from .auditable import AuditableModel

class Seguimiento(AuditableModel):
    trabajador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='seguimientos')
    profesional = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='seguimientos_registrados')
    motivo = models.CharField(max_length=500)
    categoria = models.CharField(max_length=100)
    observacion = models.TextField(max_length=10000)
    estado = models.CharField(max_length=100)
    evolucion = models.TextField(max_length=5000)
    plan_accion = models.TextField(max_length=5000)
    proxima_revision = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'saspel_seguimiento'
        ordering = ['creado_en', 'id']
        indexes = [models.Index(fields=['trabajador','creado_en'], name='saspel_seg_trab_fecha_idx')]
