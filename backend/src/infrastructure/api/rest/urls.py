"""Agrupa las rutas bajo /api/: prueba histórica, health, auth y superadmin. Para agregar un
módulo, incluir su archivo de rutas aquí y actualizar POSTMAN_PRUEBAS.md.
"""

from django.urls import include, path

from src.infrastructure.api.rest.views.health import health
from src.infrastructure.api.rest.views.prueba import prueba
from src.infrastructure.api.rest.views.nuevo_trabajador import DashboardNuevoTrabajadorView
from src.infrastructure.api.rest.views.resultados import (
    ResultadosPropiosView, DetalleResultadoPropioView, MisTrabajadoresView,
    ResultadosTrabajadorView, DetalleResultadoProfesionalView,
)
from src.infrastructure.api.rest.views.responder_evaluacion import (
    EvaluacionView, IniciarEvaluacionView, GuardarEvaluacionView, FinalizarEvaluacionView, ResultadoInicialView,
)


from src.infrastructure.api.rest.views.citas import (CitasView, ContextoCitaView, AccionCitaView, DisponibilidadView, DesactivarDisponibilidadView)

from src.infrastructure.api.rest.views.notas_cita import NotasCitaView

from src.infrastructure.api.rest.views.seguimiento import SeguimientoView

from src.infrastructure.api.rest.views.estado_animo import AnimoPropioView, AnimoProfesionalView

from src.infrastructure.api.rest.views.factores import FactoresPropiosView, FactoresProfesionalView, TiposFactorView, EditarTipoFactorView

from src.infrastructure.api.rest.views.alertas import ReglasAlertaView, DesactivarReglaView, AlertasView, AccionAlertaView

from src.infrastructure.api.rest.views.notificaciones import NotificacionesView, LeerNotificacionView

urlpatterns = [
    path('notificaciones/',NotificacionesView.as_view()),
    path('notificaciones/<uuid:notificacion_id>/leer/',LeerNotificacionView.as_view()),
    path('alertas/reglas/', ReglasAlertaView.as_view()),
    path('alertas/reglas/<uuid:regla_id>/desactivar/', DesactivarReglaView.as_view()),
    path('alertas/', AlertasView.as_view()),
    path('alertas/<uuid:alerta_id>/acciones/', AccionAlertaView.as_view()),
    path('trabajador/factores/', FactoresPropiosView.as_view()),
    path('psicologo/trabajadores/<uuid:trabajador_id>/factores/', FactoresProfesionalView.as_view()),
    path('catalogos/factores/', TiposFactorView.as_view()),
    path('catalogos/factores/<uuid:tipo_id>/', EditarTipoFactorView.as_view()),
    path('trabajador/animo/', AnimoPropioView.as_view()),
    path('psicologo/trabajadores/<uuid:trabajador_id>/animo/', AnimoProfesionalView.as_view()),
    path('psicologo/trabajadores/<uuid:trabajador_id>/seguimiento/', SeguimientoView.as_view()),
    path('citas/<uuid:cita_id>/notas/', NotasCitaView.as_view()),
    path('citas/', CitasView.as_view()),
    path('citas/contexto/', ContextoCitaView.as_view()),
    path('citas/<uuid:cita_id>/<str:accion>/', AccionCitaView.as_view()),
    path('psicologo/disponibilidad/', DisponibilidadView.as_view()),
    path('psicologo/disponibilidad/<uuid:bloque_id>/desactivar/', DesactivarDisponibilidadView.as_view()),
    path('trabajador/resultados/', ResultadosPropiosView.as_view()),
    path('trabajador/resultados/<uuid:resultado_id>/', DetalleResultadoPropioView.as_view()),
    path('psicologo/trabajadores/', MisTrabajadoresView.as_view()),
    path('psicologo/trabajadores/<uuid:trabajador_id>/resultados/', ResultadosTrabajadorView.as_view()),
    path('psicologo/resultados/<uuid:resultado_id>/', DetalleResultadoProfesionalView.as_view()),
    path('trabajador/evaluacion-inicial/resultado/', ResultadoInicialView.as_view()),
    path('nuevo-trabajador/evaluaciones/<uuid:asignacion_id>/', EvaluacionView.as_view()),
    path('nuevo-trabajador/evaluaciones/<uuid:asignacion_id>/iniciar/', IniciarEvaluacionView.as_view()),
    path('nuevo-trabajador/evaluaciones/<uuid:asignacion_id>/respuestas/', GuardarEvaluacionView.as_view()),
    path('nuevo-trabajador/evaluaciones/<uuid:asignacion_id>/finalizar/', FinalizarEvaluacionView.as_view()),
    path('nuevo-trabajador/dashboard/', DashboardNuevoTrabajadorView.as_view(), name='nuevo-trabajador-dashboard'),
    path('superadmin/', include('src.infrastructure.api.rest.superadmin_urls')),
    path('auth/', include('src.infrastructure.api.rest.auth_urls')),
    path('', prueba),
    path('health/', health, name='health'),
]
