"""Este archivo guarda las preguntas de cada versión de un cuestionario.

Una pregunta puede ofrecer opciones de una escala o pedir texto, un número o
una respuesta de sí/no. El orden permite presentarlas en la secuencia prevista
y no puede repetirse dentro del mismo instrumento. Se conservan el instrumento
y la escala asociados, y no se puede borrar una pregunta que tenga respuestas.
Más adelante se comprobará que cada respuesta corresponda al tipo esperado.
"""

from django.db import models

from .escala_respuesta import EscalaRespuesta
from .instrumento_psicologico import InstrumentoPsicologico


class PreguntaInstrumento(models.Model):
    """Pregunta ordenada dentro de una versión; describe tipo, escala e inversión para un futuro
    proceso de respuesta.
    """
    class TipoRespuesta(models.TextChoices):
        ESCALA = 'ESCALA', 'Escala'
        TEXTO = 'TEXTO', 'Texto'
        NUMERO = 'NUMERO', 'Número'
        BOOLEANO = 'BOOLEANO', 'Booleano'

    # Cuestionario y versión a los que pertenece esta pregunta.
    instrumento = models.ForeignKey(
        InstrumentoPsicologico, on_delete=models.PROTECT, related_name='preguntas',
    )
    texto = models.TextField()
    # Posición de la pregunta dentro de ese cuestionario.
    orden = models.PositiveSmallIntegerField()
    # Define si se espera elegir una opción, escribir texto, un número o sí/no.
    tipo_respuesta = models.CharField(max_length=8, choices=TipoRespuesta.choices)
    # Opciones disponibles si la pregunta usa una escala; puede quedar pendiente.
    escala = models.ForeignKey(
        EscalaRespuesta, on_delete=models.PROTECT, null=True, blank=True,
        related_name='preguntas',
    )
    # Marca preguntas que necesitarán un tratamiento distinto al calcular el puntaje; aquí no se
    # calcula.
    invertida = models.BooleanField(default=False)
    # Indica si será necesario responder esta pregunta para completar la evaluación.
    obligatoria = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saspel_pregunta_instrumento'
        verbose_name = 'pregunta de instrumento'
        verbose_name_plural = 'preguntas de instrumento'
        constraints = [
            models.UniqueConstraint(
                fields=['instrumento', 'orden'], name='saspel_pregunta_instrumento_orden_unico',
            ),
            models.CheckConstraint(
                condition=models.Q(tipo_respuesta__in=['ESCALA', 'TEXTO', 'NUMERO', 'BOOLEANO']),
                name='saspel_pregunta_tipo_valido',
            ),
        ]

    def __str__(self):
        return f'{self.orden}. {self.texto}'
