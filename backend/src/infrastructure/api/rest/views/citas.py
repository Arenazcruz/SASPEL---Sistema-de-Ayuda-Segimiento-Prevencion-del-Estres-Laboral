from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from src.domain.exceptions.superadmin import AdministrationError

from src.application.use_cases.citas import GestionarCitas
from src.infrastructure.api.rest.views.resultados import ResultadosView
from src.infrastructure.persistence.django.repositories.citas import DjangoCitasRepository


class EstrictoSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - set(self.fields):
            raise serializers.ValidationError({'detail': 'La solicitud contiene campos no admitidos.'})
        return super().to_internal_value(data)


class SolicitudSerializer(EstrictoSerializer):
    fecha_inicio = serializers.DateTimeField()
    fecha_fin = serializers.DateTimeField()
    motivo = serializers.CharField(max_length=2000)
    prioridad = serializers.ChoiceField(choices=['BAJA', 'MEDIA', 'ALTA'], default='MEDIA')


class AccionSerializer(EstrictoSerializer):
    motivo = serializers.CharField(max_length=2000, required=False, allow_blank=True, default='')


class DisponibilidadSerializer(EstrictoSerializer):
    dia_semana = serializers.IntegerField(min_value=0, max_value=6)
    hora_inicio = serializers.TimeField()
    hora_fin = serializers.TimeField()


def caso():
    return GestionarCitas(DjangoCitasRepository())


class CitasBaseView(ResultadosView):
    def handle_exception(self, exc):
        if isinstance(exc, AdministrationError):
            exc = ValidationError({'detail': str(exc)})
        return super().handle_exception(exc)


class CitasView(CitasBaseView):
    http_method_names = ['get', 'post', 'head', 'options']

    def get(self, request):
        return Response(caso().listar(request.user.pk))

    def post(self, request):
        data = SolicitudSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(caso().solicitar(request.user.pk, data.validated_data), status=201)


class ContextoCitaView(CitasBaseView):
    def get(self, request):
        return Response(caso().contexto(request.user.pk))


class AccionCitaView(CitasBaseView):
    http_method_names = ['post', 'options']

    def post(self, request, cita_id, accion):
        data = AccionSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(caso().accion(request.user.pk, cita_id, accion, data.validated_data['motivo']))


class DisponibilidadView(CitasBaseView):
    http_method_names = ['get', 'post', 'head', 'options']

    def get(self, request):
        return Response(caso().disponibilidad(request.user.pk))

    def post(self, request):
        data = DisponibilidadSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(caso().disponibilidad(request.user.pk, data.validated_data), status=201)


class DesactivarDisponibilidadView(CitasBaseView):
    http_method_names = ['post', 'options']

    def post(self, request, bloque_id):
        data = EstrictoSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(caso().disponibilidad(request.user.pk, bloque_id=bloque_id))
