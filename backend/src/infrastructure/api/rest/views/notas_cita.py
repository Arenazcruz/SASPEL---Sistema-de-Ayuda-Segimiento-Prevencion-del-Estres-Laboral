from rest_framework import serializers
from rest_framework.response import Response
from src.infrastructure.api.rest.views.citas import CitasBaseView, EstrictoSerializer
from src.application.use_cases.notas_cita import GestionarNotasCita
from src.infrastructure.persistence.django.repositories.notas_cita import DjangoNotasCitaRepository

class NotaSerializer(EstrictoSerializer):
    observacion = serializers.CharField(max_length=10000)

class NotasCitaView(CitasBaseView):
    http_method_names = ['get', 'post', 'head', 'options']

    def get(self, request, cita_id):
        return Response(GestionarNotasCita(DjangoNotasCitaRepository()).ejecutar(request.user.pk, cita_id))

    def post(self, request, cita_id):
        data = NotaSerializer(data=request.data); data.is_valid(raise_exception=True)
        return Response(GestionarNotasCita(DjangoNotasCitaRepository()).ejecutar(request.user.pk, cita_id, **data.validated_data), status=201)
