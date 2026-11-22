from rest_framework import serializers
from rest_framework.response import Response
from src.application.use_cases.recomendaciones import GestionarRecomendaciones
from src.infrastructure.api.rest.views.citas import CitasBaseView, EstrictoSerializer
from src.infrastructure.persistence.django.repositories.recomendaciones import DjangoRecomendacionesRepository


class TextoRecomendacion(EstrictoSerializer):
    compartida = serializers.BooleanField(default=False)
    texto = serializers.CharField(max_length=5000)


class EstadoRecomendacion(EstrictoSerializer):
    estado = serializers.ChoiceField(choices=['EN_PROGRESO', 'COMPLETADA', 'CANCELADA'])


class RecomendacionesPropiasView(CitasBaseView):
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        return Response(GestionarRecomendaciones(DjangoRecomendacionesRepository()).propias(request.user.pk))


class RecomendacionesView(CitasBaseView):
    http_method_names = ['get', 'post', 'head', 'options']

    def get(self, request, seguimiento_id):
        return Response(GestionarRecomendaciones(DjangoRecomendacionesRepository()).ejecutar(request.user.pk, seguimiento_id))

    def post(self, request, seguimiento_id):
        data = TextoRecomendacion(data=request.data); data.is_valid(raise_exception=True)
        return Response(GestionarRecomendaciones(DjangoRecomendacionesRepository()).ejecutar(request.user.pk, seguimiento_id, data.validated_data), status=201)


class EstadoRecomendacionView(CitasBaseView):
    http_method_names = ['post', 'options']

    def post(self, request, seguimiento_id, recomendacion_id):
        data = EstadoRecomendacion(data=request.data); data.is_valid(raise_exception=True)
        return Response(GestionarRecomendaciones(DjangoRecomendacionesRepository()).ejecutar(request.user.pk, seguimiento_id, data.validated_data, recomendacion_id))
