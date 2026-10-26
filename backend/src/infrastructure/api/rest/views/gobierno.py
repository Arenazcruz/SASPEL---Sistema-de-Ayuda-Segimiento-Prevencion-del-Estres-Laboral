from rest_framework import serializers
from rest_framework.response import Response
from src.application.use_cases.gobierno import GobiernoSistema
from src.infrastructure.api.rest.views.citas import CitasBaseView, EstrictoSerializer
from src.infrastructure.persistence.django.repositories.gobierno import DjangoGobiernoRepository


class PoliticaSerializer(EstrictoSerializer):
    tipo=serializers.ChoiceField(choices=['TERMINOS_USO','PRIVACIDAD_DATOS','CONSENTIMIENTO_EVALUACION'])
    titulo=serializers.CharField(max_length=200)
    version=serializers.CharField(max_length=50)
    contenido=serializers.CharField(max_length=100000)
    obligatoria=serializers.BooleanField(default=True)


class PoliticasAdministracionView(CitasBaseView):
    http_method_names=['get','post','head','options']

    def get(self, request):
        return Response(GobiernoSistema(DjangoGobiernoRepository()).politicas(request.user.pk))

    def post(self, request):
        data=PoliticaSerializer(data=request.data); data.is_valid(raise_exception=True)
        return Response(GobiernoSistema(DjangoGobiernoRepository()).politicas(request.user.pk,data.validated_data),status=201)


class AuditoriaFiltros(serializers.Serializer):
    desde=serializers.DateField(required=False)
    hasta=serializers.DateField(required=False)
    actor_id=serializers.UUIDField(required=False)
    entidad=serializers.CharField(max_length=200,required=False)
    accion=serializers.CharField(max_length=20,required=False)
    page=serializers.IntegerField(min_value=1,max_value=1000000,default=1)


class AuditoriaView(CitasBaseView):
    def get(self, request):
        data=AuditoriaFiltros(data=request.query_params);data.is_valid(raise_exception=True)
        return Response(GobiernoSistema(DjangoGobiernoRepository()).auditoria(request.user.pk,data.validated_data))
