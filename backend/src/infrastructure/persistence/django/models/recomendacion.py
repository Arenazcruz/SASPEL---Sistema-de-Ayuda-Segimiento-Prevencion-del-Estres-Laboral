from django.conf import settings
from django.db import models
from .auditable import AuditableModel
from .seguimiento import Seguimiento


class Recomendacion(AuditableModel):
    seguimiento = models.ForeignKey(Seguimiento, on_delete=models.PROTECT, related_name='recomendaciones')
    profesional = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='recomendaciones_registradas')
    texto = models.TextField(max_length=5000)
    estado = models.CharField(max_length=12, default='PENDIENTE', choices=[(s, s) for s in ('PENDIENTE', 'EN_PROGRESO', 'COMPLETADA', 'CANCELADA')])

    class Meta:
        db_table = 'saspel_recomendacion'
        ordering = ['creado_en', 'id']
        constraints = [models.CheckConstraint(condition=models.Q(estado__in=['PENDIENTE', 'EN_PROGRESO', 'COMPLETADA', 'CANCELADA']), name='saspel_recomendacion_estado')]
