"""Publica login/, me/ y refresh/ bajo /api/auth/. Revisar AuthService, exclusiones del
interceptor y pruebas API si cambia una dirección.
"""

from django.urls import path
from src.infrastructure.api.rest.views.auth import LoginView, MeView, RefreshView
from src.infrastructure.api.rest.views.primer_acceso import (
    AceptarPoliticasView, CambiarPasswordView, EstadoPrimerAccesoView, PoliticasPendientesView,
)

urlpatterns = [
    path('primer-acceso/', EstadoPrimerAccesoView.as_view(), name='auth-primer-acceso'),
    path('primer-acceso/password/', CambiarPasswordView.as_view(), name='auth-primer-acceso-password'),
    path('primer-acceso/politicas/', PoliticasPendientesView.as_view(), name='auth-primer-acceso-politicas'),
    path('primer-acceso/aceptar/', AceptarPoliticasView.as_view(), name='auth-primer-acceso-aceptar'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('refresh/', RefreshView.as_view(), name='auth-refresh'),
]
