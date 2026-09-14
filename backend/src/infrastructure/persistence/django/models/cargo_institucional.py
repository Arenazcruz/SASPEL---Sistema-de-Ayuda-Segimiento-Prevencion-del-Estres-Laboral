"""Este archivo guarda los cargos de la institución, como Analista.

Los perfiles usan este catálogo para indicar qué cargo ocupa cada persona.
Un cargo puede desactivarse sin perder esa información. No se permite repetir
su nombre ni borrar un cargo que todavía esté asociado a algún perfil.
El cargo no determina automáticamente el área de trabajo.
"""

from django.db import models


class CargoInstitucional(models.Model):
    # Nombre del cargo que se podrá seleccionar en el perfil.
    """Catálogo del puesto de trabajo, independiente del área institucional."""
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(blank=True)
    # Permite retirar el cargo de uso sin perder los perfiles asociados.
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saspel_cargo_institucional'
        verbose_name = 'cargo institucional'
        verbose_name_plural = 'cargos institucionales'

    def __str__(self):
        return self.nombre
