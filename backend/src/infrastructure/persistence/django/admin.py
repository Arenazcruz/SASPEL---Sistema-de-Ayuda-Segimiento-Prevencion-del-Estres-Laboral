"""Este archivo muestra los modelos de SASPEL en el administrador de Django.

Durante el desarrollo permite revisar áreas, perfiles, instrumentos, horarios
y citas. No confirma citas, reparte trabajadores ni calcula resultados por sí
solo; esas funciones se implementarán más adelante.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Usuario,
    PoliticaSistema,
    AceptacionPolitica,
    AplicacionInstrumento,
    AreaInstitucional,
    AreaCargo,
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
    AreaCargo,
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
        ('Primer acceso', {'fields': ('debe_cambiar_password',)}),
        ('Auditoría', {'fields': ('id', 'creado_en', 'actualizado_en', 'creado_por', 'actualizado_por', 'deleted')}),
    )


@admin.register(PoliticaSistema)
class PoliticaSistemaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'version', 'vigente_desde', 'obligatoria', 'activo')
    list_filter = ('tipo', 'activo', 'obligatoria')
    search_fields = ('titulo', 'version')
    readonly_fields = ('id', 'creado_en', 'actualizado_en', 'creado_por', 'actualizado_por', 'deleted')

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if obj and (obj.activo or obj.aceptaciones.exists()):
            fields += ('tipo', 'titulo', 'version', 'contenido', 'vigente_desde', 'obligatoria')
        return fields

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = str(request.user.pk)
        obj.actualizado_por = str(request.user.pk)
        super().save_model(request, obj, form, change)


@admin.register(AceptacionPolitica)
class AceptacionPoliticaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'politica', 'fecha_aceptacion')
    readonly_fields = tuple(field.name for field in AceptacionPolitica._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
