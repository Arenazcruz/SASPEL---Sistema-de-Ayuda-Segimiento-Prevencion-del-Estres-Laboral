"""Este archivo guarda una ocasión en la que se responde un cuestionario asignado.

Permite saber si se inició, finalizó o anuló, y registrar sus fechas. Cada
asignación tiene como máximo una aplicación; desde ella se conoce al trabajador
y al instrumento. Las respuestas y el resultado se guardan vinculados a esta
aplicación y evitan que se borre mientras existan. Finalizarla no calcula todavía
un resultado automáticamente.
"""

from django.db import models

from .asignacion_instrumento import AsignacionInstrumento


class AplicacionInstrumento(models.Model):
    """Intento único de respuesta por asignación; estados y fechas no ejecutan corrección
    automática.
    """
    class Estado(models.TextChoices):
        INICIADA = 'INICIADA', 'Iniciada'
        FINALIZADA = 'FINALIZADA', 'Finalizada'
        ANULADA = 'ANULADA', 'Anulada'

    # Encargo que dio lugar a esta evaluación; desde él se conoce al trabajador.
    asignacion = models.OneToOneField(
        AsignacionInstrumento, on_delete=models.PROTECT, related_name='aplicacion',
    )
    # Indica si esta evaluación se inició, finalizó o anuló.
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.INICIADA)
    # Momento en que se empezó a responder, cuando se registre.
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    # Momento en que se terminó de responder, cuando se registre.
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saspel_aplicacion_instrumento'
        verbose_name = 'aplicación de instrumento'
        verbose_name_plural = 'aplicaciones de instrumentos'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(estado__in=['INICIADA', 'FINALIZADA', 'ANULADA']),
                name='saspel_aplicacion_estado_valido',
            ),
        ]

    def __str__(self):
        return f'Aplicación de asignación {self.asignacion_id} ({self.estado})'
