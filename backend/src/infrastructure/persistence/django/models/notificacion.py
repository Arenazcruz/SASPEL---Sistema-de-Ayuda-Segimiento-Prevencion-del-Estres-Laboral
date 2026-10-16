from django.conf import settings
from django.db import models
from .auditable import AuditableModel

class Notificacion(AuditableModel):
    destinatario=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='notificaciones')
    tipo=models.CharField(max_length=30)
    titulo=models.CharField(max_length=180)
    origen_id=models.UUIDField()
    evento=models.CharField(max_length=150)
    leida_en=models.DateTimeField(null=True,blank=True)
    class Meta:
        db_table='saspel_notificacion'
        ordering=['-creado_en','-pk']
        constraints=[models.UniqueConstraint(fields=['destinatario','evento'],name='saspel_notificacion_evento_unico')]
