"""Este archivo muestra los modelos de SASPEL en el administrador de Django.

Durante el desarrollo permite revisar áreas, perfiles, instrumentos, horarios
y citas. No confirma citas, reparte trabajadores ni calcula resultados por sí
solo; esas funciones se implementarán más adelante.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Usuario,
    AplicacionInstrumento,
    AreaInstitucional,
    AsignacionInstrumento,
    AsignacionProfesional,
    CargoInstitucional,
    Cita,
    DisponibilidadPsicologo,
    EscalaRespuesta,
    InstrumentoPsicologico,
    OpcionRespuesta,
    PerfilUsuario,
    PreguntaInstrumento,
    RangoInterpretacion,
    RespuestaPregunta,
    ResultadoInstrumento,
)

admin.site.register([
    AreaInstitucional,
    CargoInstitucional,
    PerfilUsuario,
    AsignacionProfesional,
    InstrumentoPsicologico,
    EscalaRespuesta,
    OpcionRespuesta,
    PreguntaInstrumento,
    RangoInterpretacion,
    AsignacionInstrumento,
    AplicacionInstrumento,
    RespuestaPregunta,
    ResultadoInstrumento,
])
admin.site.register([DisponibilidadPsicologo, Cita])


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    readonly_fields = ('id', 'creado_en', 'actualizado_en')
    fieldsets = UserAdmin.fieldsets + (
        ('Auditoría', {'fields': ('id', 'creado_en', 'actualizado_en', 'creado_por', 'actualizado_por', 'deleted')}),
    )
