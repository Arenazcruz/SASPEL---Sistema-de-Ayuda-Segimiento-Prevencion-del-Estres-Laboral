from rest_framework import serializers
from rest_framework.response import Response
from src.infrastructure.api.rest.views.citas import CitasBaseView, EstrictoSerializer
from src.domain.entities.seguimiento import DatosSeguimiento
from src.application.use_cases.seguimiento import GestionarSeguimiento
from src.infrastructure.persistence.django.repositories.seguimiento import DjangoSeguimientoRepository

class SeguimientoSerializer(EstrictoSerializer):
    motivo = serializers.CharField(max_length=500)
    categoria = serializers.CharField(max_length=100)
    observacion = serializers.CharField(max_length=10000)
    estado = serializers.CharField(max_length=100)
    evolucion = serializers.CharField(max_length=5000)
    plan_accion = serializers.CharField(max_length=5000)
    proxima_revision = serializers.DateField(required=False, allow_null=True, default=None)

class SeguimientoView(CitasBaseView):
    http_method_names = ['get','post','head','options']

    def get(self, request, trabajador_id):
        return Response(GestionarSeguimiento(DjangoSeguimientoRepository()).ejecutar(request.user.pk,trabajador_id))

    def post(self, request, trabajador_id):
        data = SeguimientoSerializer(data=request.data); data.is_valid(raise_exception=True)
        return Response(GestionarSeguimiento(DjangoSeguimientoRepository()).ejecutar(
            request.user.pk,trabajador_id,DatosSeguimiento(**data.validated_data)), status=201)
