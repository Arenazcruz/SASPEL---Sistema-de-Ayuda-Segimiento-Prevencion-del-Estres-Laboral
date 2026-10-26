from rest_framework import serializers
from rest_framework.response import Response
from src.application.use_cases.evolucion import ConsultarEvolucion
from src.infrastructure.api.rest.views.citas import CitasBaseView
from src.infrastructure.persistence.django.repositories.evolucion import DjangoEvolucionRepository


class FiltrosEvolucion(serializers.Serializer):
    desde = serializers.DateField(required=False)
    hasta = serializers.DateField(required=False)
    instrumento_id = serializers.UUIDField(required=False)


class EvolucionView(CitasBaseView):
    def get(self, request, trabajador_id=None):
        filtros = FiltrosEvolucion(data=request.query_params)
        filtros.is_valid(raise_exception=True)
        return Response(ConsultarEvolucion(DjangoEvolucionRepository()).ejecutar(request.user.pk, trabajador_id, filtros.validated_data))
