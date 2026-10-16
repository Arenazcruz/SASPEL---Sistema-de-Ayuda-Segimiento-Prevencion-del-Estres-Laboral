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

urlpatterns = [
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
