"""Agrupa las rutas bajo /api/: prueba histórica, health, auth y superadmin. Para agregar un
módulo, incluir su archivo de rutas aquí y actualizar POSTMAN_PRUEBAS.md.
"""

from django.urls import include, path

from src.infrastructure.api.rest.views.health import health
from src.infrastructure.api.rest.views.prueba import prueba


urlpatterns = [
    path('superadmin/', include('src.infrastructure.api.rest.superadmin_urls')),
    path('auth/', include('src.infrastructure.api.rest.auth_urls')),
    path('', prueba),
    path('health/', health, name='health'),
]
