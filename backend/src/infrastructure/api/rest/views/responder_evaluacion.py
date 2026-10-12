from dataclasses import asdict

from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from src.application.dto.responder_evaluacion import RespuestaEvaluacion
from src.domain.exceptions.evaluacion import EvaluacionError, EvaluacionNoEncontrada
from src.infrastructure.api.rest.serializers.responder_evaluacion import GuardarEvaluacionSerializer, IniciarEvaluacionSerializer
from src.infrastructure.api.rest.views.nuevo_trabajador import DashboardNuevoTrabajadorView
from src.infrastructure.dependencies.responder_evaluacion import build_responder_evaluacion


class EvaluacionView(DashboardNuevoTrabajadorView):
    def handle_exception(self, exc):
        if isinstance(exc, EvaluacionNoEncontrada):
            exc = NotFound(str(exc))
        elif isinstance(exc, EvaluacionError):
            exc = ValidationError({'detail': str(exc), 'preguntas_pendientes': [str(pk) for pk in exc.pendientes]})
        return super().handle_exception(exc)

    def get(self, request, asignacion_id):
        return Response(asdict(build_responder_evaluacion().consultar(request.user.pk, asignacion_id)))


class IniciarEvaluacionView(EvaluacionView):
    http_method_names = ['post', 'options']

    def post(self, request, asignacion_id):
        serializer = IniciarEvaluacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(asdict(build_responder_evaluacion().iniciar(request.user.pk, asignacion_id)))


class GuardarEvaluacionView(EvaluacionView):
    http_method_names = ['post', 'options']

    def post(self, request, asignacion_id):
        serializer = GuardarEvaluacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers = tuple(RespuestaEvaluacion(**data) for data in serializer.validated_data['respuestas'])
        return Response(asdict(build_responder_evaluacion().guardar(request.user.pk, asignacion_id, answers)))


class FinalizarEvaluacionView(EvaluacionView):
    http_method_names = ['post', 'options']

    def post(self, request, asignacion_id):
        serializer = GuardarEvaluacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers = tuple(RespuestaEvaluacion(**data) for data in serializer.validated_data['respuestas'])
        return Response(asdict(build_responder_evaluacion().finalizar(request.user.pk, asignacion_id, answers)))
