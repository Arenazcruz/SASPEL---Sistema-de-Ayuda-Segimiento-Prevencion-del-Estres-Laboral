"""Entrada HTTP de sesión: valida request con serializers, ejecuta Application y construye JSON
sin caché. Login y refresh son públicos; me exige JWT. Cambiar el formato aquí requiere
revisar AuthService y POSTMAN_PRUEBAS.md.
"""

from dataclasses import asdict
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from src.application.dto.auth import LoginCommand
from src.application.services.auth_identity import (
    InactiveAccount, InvalidCredentials, MissingFunctionalRole,
)
from src.infrastructure.api.rest.serializers.auth import LoginSerializer, RefreshSerializer
from src.infrastructure.auth.jwt_token_provider import JWTTokenProvider
from src.infrastructure.dependencies.auth import build_authentication, build_current_identity


class AuthErrorMixin:
    """Mantiene el mismo mensaje cuando el correo o la contraseña son incorrectos."""

    def handle_exception(self, exc):
        """Traduce credenciales inválidas a 401 y cuenta inactiva/sin rol a 403; delega otros
        errores a DRF sin revelar si un correo existe.
        """
        if isinstance(exc, InvalidCredentials):
            exc = AuthenticationFailed('Correo o contraseña incorrectos.')
        elif isinstance(exc, InactiveAccount):
            exc = PermissionDenied('Esta cuenta no está habilitada para ingresar.')
        elif isinstance(exc, MissingFunctionalRole):
            exc = PermissionDenied('Tu cuenta aún no tiene un rol de acceso asignado.')
        return super().handle_exception(exc)


class LoginView(AuthErrorMixin, APIView):
    """POST /api/auth/login/: valida correo y clave, obtiene identidad y emite tokens."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_authenticate_header(self, request):
        return 'Bearer'

    def post(self, request):
        """Recibe request con email/password y devuelve 200 con access, refresh, user y
        dashboard_path separado. El proveedor actualiza last_login; una identidad sin rol no
        llega a emitir tokens.
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = build_authentication().execute(LoginCommand(**serializer.validated_data))
        identity = asdict(user)
        dashboard_path = identity.pop('dashboard_path')
        return Response({
            **JWTTokenProvider.issue(user.id), 'user': identity,
            'dashboard_path': dashboard_path,
        }, status=status.HTTP_200_OK, headers={'Cache-Control': 'no-store'})


class MeView(AuthErrorMixin, APIView):
    """GET /api/auth/me/: expone la identidad vigente de la cuenta autenticada por JWT."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        """Usa request.user.pk y devuelve DTO con dashboard_path dentro del objeto; propaga
        errores de actividad/rol mediante AuthErrorMixin.
        """
        user = build_current_identity().execute(request.user.pk)
        return Response(asdict(user), headers={'Cache-Control': 'no-store'})


class RefreshView(APIView):
    """POST /api/auth/refresh/: valida el refresh recibido y solicita un nuevo access."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_authenticate_header(self, request):
        return 'Bearer'

    def post(self, request):
        """Recibe refresh en JSON y devuelve access con no-store. La validación criptográfica y
        de cuenta activa ocurre en JWTTokenProvider, no en el serializer.
        """
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            JWTTokenProvider.renew(serializer.validated_data['refresh']),
            headers={'Cache-Control': 'no-store'},
        )
