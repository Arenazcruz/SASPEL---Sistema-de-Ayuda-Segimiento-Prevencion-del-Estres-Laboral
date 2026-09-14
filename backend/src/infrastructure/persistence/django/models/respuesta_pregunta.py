"""Este archivo guarda la respuesta que un trabajador dio a una pregunta
durante una aplicación de un instrumento.

Puede guardar una opción elegida, un texto, un número o un valor de sí/no.
Una pregunta solo tiene una respuesta por aplicación, pero puede responderse
otra vez en una evaluación posterior. Se conservan la aplicación, la pregunta
y la opción utilizadas. Más adelante se comprobará que el valor guardado sea
del tipo que pide la pregunta y que corresponda al cuestionario aplicado.
"""

from django.db import models

from .aplicacion_instrumento import AplicacionInstrumento
from .opcion_respuesta import OpcionRespuesta
from .pregunta_instrumento import PreguntaInstrumento


class RespuestaPregunta(models.Model):
    # Evaluación en la que el trabajador dio esta respuesta.
    """Respuesta única por pregunta y aplicación; conserva opción, texto, número o booleano sin
    validar todavía su correspondencia con el tipo.
    """
    aplicacion = models.ForeignKey(
        AplicacionInstrumento, on_delete=models.PROTECT, related_name='respuestas',
    )
    # Pregunta que se está respondiendo; su texto se consulta desde aquí.
    pregunta = models.ForeignKey(
        PreguntaInstrumento, on_delete=models.PROTECT, related_name='respuestas',
    )
    # Opción elegida cuando la pregunta ofrece una escala.
    opcion = models.ForeignKey(
        OpcionRespuesta, on_delete=models.PROTECT, null=True, blank=True,
        related_name='respuestas',
    )
    # Respuesta escrita libremente por el trabajador.
    valor_texto = models.TextField(null=True, blank=True)
    # Número respondido, con hasta cuatro decimales.
    valor_numerico = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    # Respuesta de sí/no; vacío significa que ese dato no se proporcionó.
    valor_booleano = models.BooleanField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saspel_respuesta_pregunta'
        verbose_name = 'respuesta a pregunta'
        verbose_name_plural = 'respuestas a preguntas'
        constraints = [
            models.UniqueConstraint(
                fields=['aplicacion', 'pregunta'], name='saspel_respuesta_aplicacion_pregunta_unica',
            ),
        ]

    def __str__(self):
        return f'Respuesta: aplicación {self.aplicacion_id}, pregunta {self.pregunta_id}'
