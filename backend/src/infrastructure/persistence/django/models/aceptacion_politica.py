from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .auditable import AuditableModel
from .politica_sistema import HistorialPoliticasQuerySet, PoliticaSistema


class AceptacionPolitica(AuditableModel):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='aceptaciones_politicas')
    politica = models.ForeignKey(PoliticaSistema, on_delete=models.PROTECT, related_name='aceptaciones')
    fecha_aceptacion = models.DateTimeField(default=timezone.now, editable=False)
    objects = HistorialPoliticasQuerySet.as_manager()

    class Meta:
        db_table = 'saspel_aceptacion_politica'
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'politica'], name='aceptacion_usuario_politica_unica'),
        ]

    def delete(self, *args, **kwargs):
        raise ValidationError('Las aceptaciones se conservan como historial.')
