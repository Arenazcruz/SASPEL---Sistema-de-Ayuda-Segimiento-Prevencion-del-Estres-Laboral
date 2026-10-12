from dataclasses import asdict

from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from src.application.dto.primer_acceso import AceptarPoliticasCommand, CambiarPasswordCommand
from src.domain.exceptions.primer_acceso import PrimerAccesoError
from src.domain.exceptions.superadmin import AdministrationError
from src.infrastructure.api.rest.serializers.primer_acceso import (
    AceptarPoliticasSerializer, CambiarPasswordSerializer,
)
from src.infrastructure.api.rest.views.auth import AuthErrorMixin
from src.infrastructure.auth.jwt_authentication import UUIDJWTAuthentication
from src.infrastructure.dependencies.primer_acceso import build_primer_acceso
from rest_framework.views import APIView


class PrimerAccesoView(AuthErrorMixin, APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [UUIDJWTAuthentication]

    def handle_exception(self, exc):
        if isinstance(exc, (PrimerAccesoError, AdministrationError)):
            exc = ValidationError({exc.field: [str(exc)]})
        return super().handle_exception(exc)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'no-store'
        return response


class EstadoPrimerAccesoView(PrimerAccesoView):
    def get(self, request):
        return Response(asdict(build_primer_acceso().estado(request.user.pk)))


class CambiarPasswordView(PrimerAccesoView):
    def post(self, request):
        serializer = CambiarPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        command = CambiarPasswordCommand(request.user.pk, **serializer.validated_data)
        return Response(asdict(build_primer_acceso().cambiar_password(command)))


class PoliticasPendientesView(PrimerAccesoView):
    def get(self, request):
        return Response([asdict(p) for p in build_primer_acceso().pendientes(request.user.pk)])


class AceptarPoliticasView(PrimerAccesoView):
    def post(self, request):
        serializer = AceptarPoliticasSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        command = AceptarPoliticasCommand(request.user.pk, tuple(serializer.validated_data['politicas']))
        return Response(asdict(build_primer_acceso().aceptar(command)))
