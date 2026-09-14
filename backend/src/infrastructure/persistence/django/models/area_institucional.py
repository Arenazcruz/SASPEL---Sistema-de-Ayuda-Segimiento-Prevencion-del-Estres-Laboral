"""Este archivo guarda las áreas de la institución, como Administración.

Cada perfil puede indicar el área en la que trabaja la persona. Un área puede
desactivarse cuando deja de utilizarse, conservando los perfiles que la señalan.
No se permite repetir el mismo nombre ni borrar un área que tenga perfiles
asociados. Los perfiles consultan su nombre desde este registro.
"""

from django.db import models


class AreaInstitucional(models.Model):
    # Nombre que se mostrará al elegir el área de un trabajador.
    """Catálogo del área de trabajo; la desactivación conserva los perfiles asociados."""
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(blank=True)
    # Permite dejar de ofrecer el área sin borrar los perfiles que la usan.
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saspel_area_institucional'
        verbose_name = 'área institucional'
        verbose_name_plural = 'áreas institucionales'

    def __str__(self):
        return self.nombre
