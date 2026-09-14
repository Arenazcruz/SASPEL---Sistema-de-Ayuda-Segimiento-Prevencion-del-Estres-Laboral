"""Este archivo completa la información laboral y personal de cada usuario.

Por ejemplo, permite guardar su código de empleado, área, cargo y teléfono.
Los nombres principales, correo y contraseña siguen en la cuenta de Django.
Cada usuario puede tener un solo perfil y cada código de empleado es único.

El perfil se elimina si se borra su cuenta, siempre que otros registros del
sistema permitan ese borrado. Un área o cargo en uso se conserva. Más adelante,
el sistema utilizará estos datos para el proceso inicial y las asignaciones.
"""

from django.conf import settings
from django.db import models

from .area_institucional import AreaInstitucional
from .cargo_institucional import CargoInstitucional


class PerfilUsuario(models.Model):
    """Extiende User con datos laborales y personales; acceso activo, tamizaje y habilitación de
    asignaciones son indicadores distintos.
    """
    class Sexo(models.TextChoices):
        FEMENINO = 'F', 'Femenino'
        MASCULINO = 'M', 'Masculino'
        OTRO = 'O', 'Otro'

    # Cuenta a la que pertenece este perfil; sus datos de acceso siguen en Django.
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_usuario',
    )
    # Identificador institucional del empleado, distinto del nombre de acceso.
    codigo_empleado = models.CharField(max_length=50, unique=True)
    # Completa el apellido que no se guarda en los campos principales de la cuenta.
    apellido_materno = models.CharField(max_length=150, blank=True)
    # Nombre con el que la persona prefiere ser llamada.
    nombre_preferido = models.CharField(max_length=150, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    # Dato opcional: femenino, masculino u otro; puede dejarse sin completar.
    sexo = models.CharField(max_length=1, choices=Sexo.choices, blank=True)
    # Número de contacto; se guarda como texto para admitir prefijos y símbolos.
    telefono = models.CharField(max_length=30, blank=True)
    # Área donde trabaja la persona; puede completarse más adelante.
    area = models.ForeignKey(
        AreaInstitucional,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='perfiles',
    )
    # Cargo que ocupa la persona dentro de la institución.
    cargo = models.ForeignKey(
        CargoInstitucional,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='perfiles',
    )
    # Indica si ya terminó la evaluación inicial; no realiza la evaluación.
    tamizaje_resuelto = models.BooleanField(default=False)
    # Por ejemplo, permite que un psicólogo de vacaciones deje de recibir nuevos trabajadores
    # sin desactivar su cuenta.
    habilitado_asignaciones = models.BooleanField(
        default=True,
        help_text='Permite recibir nuevas asignaciones sin cambiar el estado del usuario.',
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saspel_perfil_usuario'
        verbose_name = 'perfil de usuario'
        verbose_name_plural = 'perfiles de usuario'

    def __str__(self):
        return self.codigo_empleado
