import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class EventoAuditoria(models.Model):
    """Metadatos inmutables; nunca almacena contraseñas, tokens ni contenido clínico."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='eventos_auditoria')
    fecha = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(max_length=20)
    entidad = models.CharField(max_length=200)
    entidad_id = models.UUIDField(null=True)
    estado = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'saspel_evento_auditoria'
        ordering = ['-fecha', '-id']
        indexes = [models.Index(fields=['actor', 'fecha'], name='saspel_audit_actor_fecha')]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Los eventos de auditoría son inmutables.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Los eventos de auditoría se conservan.')
