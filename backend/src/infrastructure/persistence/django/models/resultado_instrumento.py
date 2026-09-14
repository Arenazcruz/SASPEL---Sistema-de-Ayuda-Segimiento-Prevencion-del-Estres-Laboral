"""Este archivo guarda el resultado obtenido en una aplicación de un cuestionario.

Registra el puntaje total, cuándo se calculó y el rango que lo describe, si ya
se conoce. Cada aplicación puede tener un solo resultado. El trabajador y el
cuestionario se conocen desde la aplicación, y la explicación se consulta en
el rango. Esos registros asociados se conservan. Por ahora se guarda el puntaje
proporcionado; su cálculo automático se implementará más adelante.
"""

from django.db import models

from .aplicacion_instrumento import AplicacionInstrumento
from .rango_interpretacion import RangoInterpretacion


class ResultadoInstrumento(models.Model):
    # Evaluación a la que pertenece el resultado; solo puede tener uno.
    """Resultado único de una aplicación con puntaje y rango opcional; requiere que otro proceso
    lo calcule y guarde.
    """
    aplicacion = models.OneToOneField(
        AplicacionInstrumento, on_delete=models.PROTECT, related_name='resultado',
    )
    # Puntaje recibido para guardar; este archivo no suma las respuestas.
    puntaje_total = models.DecimalField(max_digits=12, decimal_places=4)
    # Rango que describe el resultado, si ya se ha identificado.
    rango = models.ForeignKey(
        RangoInterpretacion, on_delete=models.PROTECT, null=True, blank=True,
        related_name='resultados',
    )
    # Momento en que se calculó el puntaje, distinto del momento de guardarlo.
    fecha_calculo = models.DateTimeField()
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saspel_resultado_instrumento'
        verbose_name = 'resultado de instrumento'
        verbose_name_plural = 'resultados de instrumentos'

    def __str__(self):
        return f'Resultado de aplicación {self.aplicacion_id}: {self.puntaje_total}'
