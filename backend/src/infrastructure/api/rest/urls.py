"""Agrupa las rutas bajo /api/: prueba histórica, health, auth y superadmin. Para agregar un
módulo, incluir su archivo de rutas aquí y actualizar POSTMAN_PRUEBAS.md.
"""

from django.urls import include, path

from src.infrastructure.api.rest.views.health import health
from src.infrastructure.api.rest.views.prueba import prueba
from src.infrastructure.api.rest.views.nuevo_trabajador import DashboardNuevoTrabajadorView
from src.infrastructure.api.rest.views.responder_evaluacion import (
    EvaluacionView, IniciarEvaluacionView, GuardarEvaluacionView, FinalizarEvaluacionView, ResultadoInicialView,
)


urlpatterns = [
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
