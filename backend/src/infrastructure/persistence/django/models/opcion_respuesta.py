"""Este archivo guarda cada opción que se puede elegir dentro de una escala.

Por ejemplo, una opción podría mostrar Nunca y tener el valor 0. El orden indica
dónde aparece al presentar las respuestas. Dentro de una escala no se repiten
el orden ni el valor, aunque otras escalas pueden usarlos. Se conserva la escala
de la opción y no se puede borrar una opción que ya tenga respuestas asociadas.
Este archivo no calcula el resultado del cuestionario.
"""

from django.db import models

from .escala_respuesta import EscalaRespuesta


class OpcionRespuesta(models.Model):
    # Conjunto de respuestas al que pertenece esta opción.
    """Opción de una escala con orden y valor propios; ese valor no calcula resultados por sí
    solo.
    """
    escala = models.ForeignKey(
        EscalaRespuesta, on_delete=models.PROTECT, related_name='opciones',
    )
    # Texto que verá el trabajador, por ejemplo Nunca.
    etiqueta = models.CharField(max_length=150)
    # Valor asociado a la opción; el cálculo de resultados se añadirá después.
    valor = models.SmallIntegerField()
    # Posición en la que se presentará la opción dentro de su escala.
    orden = models.PositiveSmallIntegerField()
    # Permite retirar una opción de uso sin borrar las respuestas que la eligieron.
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saspel_opcion_respuesta'
        verbose_name = 'opción de respuesta'
        verbose_name_plural = 'opciones de respuesta'
        constraints = [
            models.UniqueConstraint(
                fields=['escala', 'orden'], name='saspel_opcion_escala_orden_unico',
            ),
            models.UniqueConstraint(
                fields=['escala', 'valor'], name='saspel_opcion_escala_valor_unico',
            ),
        ]

    def __str__(self):
        return f'{self.etiqueta} ({self.valor})'
