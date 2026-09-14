"""Este archivo guarda los rangos usados para describir el resultado de un
cuestionario y su versión.

Por ejemplo, un rango puede abarcar de 0 a 10 y tener una explicación para ese
intervalo. El mínimo no puede superar al máximo. Los nombres y órdenes no se
repiten dentro del mismo instrumento. Un resultado consulta aquí su descripción,
por lo que un rango utilizado no se puede borrar. Más adelante se comprobará
que los rangos no se superpongan y se elegirá el adecuado para cada resultado.
"""

from django.db import models

from .instrumento_psicologico import InstrumentoPsicologico


class RangoInterpretacion(models.Model):
    # Cuestionario y versión para los que se define este rango.
    """Intervalo y etiqueta de interpretación de una versión; aquí se guardan límites, no se
    clasifican resultados.
    """
    instrumento = models.ForeignKey(
        InstrumentoPsicologico, on_delete=models.PROTECT, related_name='rangos',
    )
    nombre = models.CharField(max_length=150)
    # Puntaje desde el que comienza el rango.
    puntaje_minimo = models.IntegerField()
    # Puntaje hasta el que llega el rango.
    puntaje_maximo = models.IntegerField()
    # Explicación que podrá acompañar a un resultado clasificado en este rango.
    interpretacion = models.TextField(blank=True)
    # Posición del rango al mostrar los niveles del cuestionario.
    orden = models.PositiveSmallIntegerField()
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saspel_rango_interpretacion'
        verbose_name = 'rango de interpretación'
        verbose_name_plural = 'rangos de interpretación'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(puntaje_minimo__lte=models.F('puntaje_maximo')),
                name='saspel_rango_limites_validos',
            ),
            models.UniqueConstraint(
                fields=['instrumento', 'nombre'], name='saspel_rango_instrumento_nombre_unico',
            ),
            models.UniqueConstraint(
                fields=['instrumento', 'orden'], name='saspel_rango_instrumento_orden_unico',
            ),
        ]

    def __str__(self):
        return f'{self.nombre} [{self.puntaje_minimo}, {self.puntaje_maximo}]'
