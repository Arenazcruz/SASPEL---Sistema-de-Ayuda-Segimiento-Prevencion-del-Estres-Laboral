from dataclasses import asdict

from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from src.application.services.auth_identity import MissingFunctionalRole, present_identity
from src.infrastructure.api.rest.permissions import PrimerAccesoCompleto
from src.infrastructure.auth.django_auth_provider import DjangoAuthProvider
from src.infrastructure.auth.jwt_authentication import UUIDJWTAuthentication
from src.infrastructure.dependencies.nuevo_trabajador import build_dashboard_nuevo_trabajador


class IsNuevoTrabajador(BasePermission):
    message = 'Esta función requiere el rol NUEVO_TRABAJADOR.'

    def has_permission(self, request, view):
        try:
            return present_identity(DjangoAuthProvider._identity(request.user)).role == 'NUEVO_TRABAJADOR'
        except MissingFunctionalRole:
            return False


class DashboardNuevoTrabajadorView(APIView):
    authentication_classes = [UUIDJWTAuthentication]
    permission_classes = [IsAuthenticated, IsNuevoTrabajador, PrimerAccesoCompleto]

    def get(self, request):
        return Response(asdict(build_dashboard_nuevo_trabajador().execute(request.user.pk)))

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'no-store'
        return response
