"""Este archivo registra qué cuestionario debe responder un trabajador.

También indica si lo asignó el sistema o un profesional y cuándo debería
completarse. El mismo trabajador puede recibir el mismo cuestionario en enero
y nuevamente en abril: son evaluaciones independientes. Cada asignación puede
tener una sola aplicación. Se conservan el instrumento y los usuarios asociados.
Más adelante se implementarán la asignación y sus cambios de estado.
"""

from django.conf import settings
from django.db import models

from .instrumento_psicologico import InstrumentoPsicologico


class AsignacionInstrumento(models.Model):
    """Encargo de un instrumento versionado a un trabajador; admite nuevas evaluaciones del mismo
    instrumento.
    """
    class Origen(models.TextChoices):
        SISTEMA = 'SISTEMA', 'Sistema'
        PROFESIONAL = 'PROFESIONAL', 'Profesional'

    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        EN_PROGRESO = 'EN_PROGRESO', 'En progreso'
        COMPLETADA = 'COMPLETADA', 'Completada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    # Persona que deberá responder el cuestionario.
    trabajador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='asignaciones_de_instrumentos',
    )
    # Versión concreta que se le pide responder.
    instrumento = models.ForeignKey(
        InstrumentoPsicologico, on_delete=models.PROTECT, related_name='asignaciones',
    )
    # Persona que encargó la evaluación; puede estar vacío si la origina el sistema.
    asignado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name='asignaciones_de_instrumentos_creadas',
    )
    # Distingue un encargo del SISTEMA de uno realizado por un PROFESIONAL.
    origen = models.CharField(max_length=11, choices=Origen.choices)
    # Indica si la tarea está pendiente, en progreso, completada o cancelada.
    estado = models.CharField(max_length=11, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    # Fecha límite prevista para responder, si se ha establecido alguna.
    fecha_limite = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saspel_asignacion_instrumento'
        verbose_name = 'asignación de instrumento'
        verbose_name_plural = 'asignaciones de instrumentos'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(origen__in=['SISTEMA', 'PROFESIONAL']),
                name='saspel_asig_instrumento_origen_valido',
            ),
            models.CheckConstraint(
                condition=models.Q(estado__in=['PENDIENTE', 'EN_PROGRESO', 'COMPLETADA', 'CANCELADA']),
                name='saspel_asig_instrumento_estado_valido',
            ),
        ]

    def __str__(self):
        return f'Asignación {self.pk}: {self.trabajador_id} → {self.instrumento_id}'
