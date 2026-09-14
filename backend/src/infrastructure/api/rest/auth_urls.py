"""Publica login/, me/ y refresh/ bajo /api/auth/. Revisar AuthService, exclusiones del
interceptor y pruebas API si cambia una dirección.
"""

from django.urls import path
from src.infrastructure.api.rest.views.auth import LoginView, MeView, RefreshView

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth-login'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('refresh/', RefreshView.as_view(), name='auth-refresh'),
]
