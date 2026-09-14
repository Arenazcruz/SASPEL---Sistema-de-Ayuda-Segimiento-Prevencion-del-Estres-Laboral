"""Punto de entrada de las URLs Django: /admin/ abre el administrador y /api/ delega en
infrastructure/api/rest/urls.py. Añadir endpoints de SASPEL en ese adaptador; Angular tiene su
propio mapa de navegación.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('src.infrastructure.api.rest.urls')),
]
