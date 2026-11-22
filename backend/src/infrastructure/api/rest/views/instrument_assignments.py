from dataclasses import asdict
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from src.application.dto.responder_evaluacion import RespuestaEvaluacion
from src.application.use_cases.instrument_assignments import GestionarAsignacionesInstrumento
from src.infrastructure.api.rest.permissions import PrimerAccesoCompleto
from src.infrastructure.api.rest.views.citas import CitasBaseView, EstrictoSerializer
from src.infrastructure.api.rest.views.responder_evaluacion import EvaluacionView, IsTrabajadorEvaluacion
from src.infrastructure.api.rest.serializers.responder_evaluacion import GuardarEvaluacionSerializer, IniciarEvaluacionSerializer
from src.infrastructure.dependencies.responder_evaluacion import build_responder_instrumento
from src.infrastructure.persistence.django.repositories.instrument_assignments import DjangoInstrumentAssignmentsRepository


class AsignarInstrumentoSerializer(EstrictoSerializer):
    instrumento_id = serializers.UUIDField()
    fecha_limite = serializers.DateTimeField(required=False, allow_null=True)


class AsignacionesInstrumentoView(CitasBaseView):
    http_method_names = ['get', 'post', 'head', 'options']

    def get(self, request, trabajador_id=None):
        return Response(GestionarAsignacionesInstrumento(DjangoInstrumentAssignmentsRepository()).ejecutar(request.user.pk, trabajador_id))

    def post(self, request, trabajador_id):
        data = AsignarInstrumentoSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(GestionarAsignacionesInstrumento(DjangoInstrumentAssignmentsRepository()).ejecutar(request.user.pk, trabajador_id, data.validated_data), status=201)


class InstrumentosPropiosView(AsignacionesInstrumentoView):
    http_method_names = ['get', 'head', 'options']


class ResolverInstrumentoView(EvaluacionView):
    permission_classes = [IsAuthenticated, IsTrabajadorEvaluacion, PrimerAccesoCompleto]

    def get(self, request, asignacion_id):
        return Response(asdict(build_responder_instrumento().consultar(request.user.pk, asignacion_id)))


class AccionInstrumentoView(ResolverInstrumentoView):
    http_method_names = ['post', 'options']

    def post(self, request, asignacion_id, accion):
        from rest_framework.exceptions import NotFound
        if accion not in ('iniciar', 'respuestas', 'finalizar'):
            raise NotFound()
        caso = build_responder_instrumento()
        data = (IniciarEvaluacionSerializer if accion == 'iniciar' else GuardarEvaluacionSerializer)(data=request.data)
        data.is_valid(raise_exception=True)
        if accion == 'iniciar':
            result = caso.iniciar(request.user.pk, asignacion_id)
        else:
            respuestas = tuple(RespuestaEvaluacion(**r) for r in data.validated_data['respuestas'])
            result = (caso.guardar if accion == 'respuestas' else caso.finalizar)(request.user.pk, asignacion_id, respuestas)
        return Response(asdict(result))
