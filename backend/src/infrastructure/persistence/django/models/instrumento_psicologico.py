"""Este archivo guarda la información general de cada cuestionario psicológico
utilizado por SASPEL.

Incluye su nombre, instrucciones y versión. Por ejemplo, una versión 2.0 puede
guardarse por separado para que las evaluaciones anteriores sigan vinculadas
a la 1.0. No se permite repetir la misma combinación de código y versión.
Sus preguntas, rangos y asignaciones se conectan con este registro. No se puede
borrar mientras tenga esos registros asociados; la gestión de nuevas versiones
se implementará más adelante.
"""

from django.db import models


class InstrumentoPsicologico(models.Model):
    # Código corto que identifica el cuestionario a través de sus versiones.
    """Versión concreta del cuestionario, identificada por código y versión para conservar
    evaluaciones anteriores.
    """
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=200)
    # Distingue ediciones del mismo cuestionario, como 1.0 y 2.0.
    version = models.CharField(max_length=50, default='1.0')
    descripcion = models.TextField(blank=True)
    # Indicaciones que necesitará leer la persona antes de responder.
    instrucciones = models.TextField(blank=True)
    # Señala si el cuestionario está destinado a la evaluación inicial.
    es_inicial = models.BooleanField(default=False)
    # Permite dejar de utilizar esta versión sin borrar las evaluaciones anteriores.
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saspel_instrumento_psicologico'
        verbose_name = 'instrumento psicológico'
        verbose_name_plural = 'instrumentos psicológicos'
        constraints = [
            models.UniqueConstraint(
                fields=['codigo', 'version'],
                name='saspel_instrumento_codigo_version_unico',
            ),
        ]

    def __str__(self):
        return f'{self.codigo} / {self.version}: {self.nombre}'
