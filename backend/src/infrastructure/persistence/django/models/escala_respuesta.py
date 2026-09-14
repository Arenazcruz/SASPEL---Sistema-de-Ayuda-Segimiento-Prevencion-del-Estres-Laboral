"""Este archivo guarda los conjuntos de respuestas que pueden usar las preguntas.

Por ejemplo, una escala de frecuencia podría ofrecer varias opciones desde
Nunca hasta Siempre. Las opciones se guardan por separado y varias preguntas
pueden compartir la misma escala. Su nombre no puede repetirse y no se puede
borrar mientras existan preguntas u opciones asociadas. Estos ejemplos no
insertan escalas reales en la base de datos.
"""

from django.db import models


class EscalaRespuesta(models.Model):
    # Nombre para reconocer el conjunto de opciones al preparar una pregunta.
    """Conjunto reutilizable de opciones para preguntas; retirar su uso conserva referencias."""
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(blank=True)
    # Permite dejar de ofrecer la escala sin borrar sus opciones y preguntas.
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saspel_escala_respuesta'
        verbose_name = 'escala de respuesta'
        verbose_name_plural = 'escalas de respuesta'

    def __str__(self):
        return self.nombre
