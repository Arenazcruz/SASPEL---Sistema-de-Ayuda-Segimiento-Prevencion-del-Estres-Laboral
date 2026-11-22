from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from .auditable import AuditableModel


class HistorialPoliticasQuerySet(models.QuerySet):
    def delete(self):
        raise ValidationError('El historial de políticas no se elimina. Desactiva la política.')


class PoliticaSistema(AuditableModel):
    class Tipo(models.TextChoices):
        TERMINOS_USO = 'TERMINOS_USO', 'Términos de uso'
        PRIVACIDAD_DATOS = 'PRIVACIDAD_DATOS', 'Privacidad de datos'
        CONSENTIMIENTO_EVALUACION = 'CONSENTIMIENTO_EVALUACION', 'Consentimiento de evaluación'

    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    titulo = models.CharField(max_length=200)
    version = models.CharField(max_length=50)
    contenido = models.TextField()
    vigente_desde = models.DateTimeField(default=timezone.now)
    obligatoria = models.BooleanField(default=True)
    activo = models.BooleanField(default=False)
    objects = HistorialPoliticasQuerySet.as_manager()

    class Meta:
        db_table = 'saspel_politica_sistema'
        ordering = ('tipo', 'vigente_desde', 'id')
        constraints = [
            models.UniqueConstraint(fields=['tipo', 'version'], name='politica_tipo_version_unica'),
            models.UniqueConstraint(fields=['tipo'], condition=models.Q(activo=True), name='politica_tipo_activo_unico'),
            models.CheckConstraint(condition=models.Q(tipo__in=[
                'TERMINOS_USO', 'PRIVACIDAD_DATOS', 'CONSENTIMIENTO_EVALUACION',
            ]), name='politica_tipo_valido'),
            models.CheckConstraint(condition=~models.Q(activo=True, deleted=True), name='politica_activa_no_deleted'),
        ]

    def clean(self):
        super().clean()
        previous = type(self).objects.filter(pk=self.pk).first()
        if previous and (previous.activo or previous.aceptaciones.exists()):
            fields = ('tipo', 'titulo', 'version', 'contenido', 'vigente_desde', 'obligatoria')
            if any(getattr(previous, name) != getattr(self, name) for name in fields):
                raise ValidationError('Crea una nueva versión para modificar una política publicada o aceptada.')

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # Serializa ediciones con la aceptación de la misma versión.
            list(type(self).objects.select_for_update().filter(pk=self.pk))
            self.full_clean()
            return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Las políticas se conservan. Usa activo=False para retirarlas.')

    def __str__(self):
        return f'{self.titulo} · {self.version}'
