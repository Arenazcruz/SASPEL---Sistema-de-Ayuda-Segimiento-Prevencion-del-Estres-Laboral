from django.conf import settings
from django.db import models
from .auditable import AuditableModel

class NotaCita(AuditableModel):
    cita = models.ForeignKey('api.Cita', on_delete=models.PROTECT, related_name='notas')
    profesional = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='notas_cita')
    observacion = models.TextField(max_length=10000)

    class Meta:
        db_table = 'saspel_nota_cita'
        ordering = ['creado_en', 'id']
