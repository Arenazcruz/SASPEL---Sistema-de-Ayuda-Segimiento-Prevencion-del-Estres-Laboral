from dataclasses import asdict

from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from src.domain.exceptions.resultados import AccesoResultadosDenegado, ResultadoNoDisponible
from src.domain.exceptions.superadmin import AdministrationError
from src.infrastructure.api.rest.permissions import PrimerAccesoCompleto
from src.infrastructure.dependencies.resultados import build_resultados


class ResultadosView(APIView):
    permission_classes = [IsAuthenticated, PrimerAccesoCompleto]
    http_method_names = ['get', 'head', 'options']

    def handle_exception(self, exc):
        if isinstance(exc, AccesoResultadosDenegado):
            exc = PermissionDenied(str(exc))
        elif isinstance(exc, ResultadoNoDisponible):
            exc = NotFound(str(exc))
        elif isinstance(exc, AdministrationError):
            exc = ValidationError('No se pudo consultar la información. Intenta nuevamente.')
        return super().handle_exception(exc)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'no-store'
        return response


class ResultadosPropiosView(ResultadosView):
    def get(self, request):
        return Response([asdict(row) for row in build_resultados().propios(request.user.pk)])


class DetalleResultadoPropioView(ResultadosView):
    def get(self, request, resultado_id):
        return Response(asdict(build_resultados().detalle_propio(request.user.pk, resultado_id)))


class MisTrabajadoresView(ResultadosView):
    def get(self, request):
        return Response(asdict(build_resultados().trabajadores(request.user.pk)))


class ResultadosTrabajadorView(ResultadosView):
    def get(self, request, trabajador_id):
        return Response([asdict(row) for row in build_resultados().de_trabajador(request.user.pk, trabajador_id)])


class DetalleResultadoProfesionalView(ResultadosView):
    def get(self, request, resultado_id):
        return Response(asdict(build_resultados().detalle_profesional(request.user.pk, resultado_id)))
