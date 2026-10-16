from rest_framework import serializers
from rest_framework.response import Response
from src.infrastructure.api.rest.views.citas import CitasBaseView, EstrictoSerializer
from src.domain.entities.factor_psicosocial import DatosFactor
from src.application.use_cases.factores import GestionarFactores
from src.infrastructure.persistence.django.repositories.factores import DjangoFactoresRepository

def caso():
    return GestionarFactores(DjangoFactoresRepository())

class FactorSerializer(EstrictoSerializer):
    tipo_id = serializers.UUIDField()
    nivel = serializers.CharField(max_length=100)
    descripcion = serializers.CharField(max_length=3000)

class TipoSerializer(EstrictoSerializer):
    nombre = serializers.CharField(max_length=120)
    descripcion = serializers.CharField(max_length=1000,required=False,allow_blank=True,default='')
    activo = serializers.BooleanField(default=True)

class FactoresPropiosView(CitasBaseView):
    http_method_names = ['get','post','head','options']
    def get(self, request):
        return Response(caso().ejecutar(request.user.pk))
    def post(self, request):
        data=FactorSerializer(data=request.data);data.is_valid(raise_exception=True)
        return Response(caso().ejecutar(request.user.pk,datos=DatosFactor(**data.validated_data)),status=201)

class FactoresProfesionalView(CitasBaseView):
    def get(self, request, trabajador_id):
        return Response(caso().ejecutar(request.user.pk,trabajador_id))

class TiposFactorView(CitasBaseView):
    http_method_names = ['get','post','head','options']
    def get(self, request):
        return Response(caso().catalogo(request.user.pk))
    def post(self, request):
        data=TipoSerializer(data=request.data);data.is_valid(raise_exception=True)
        return Response(caso().catalogo(request.user.pk,data.validated_data),status=201)

class EditarTipoFactorView(CitasBaseView):
    http_method_names = ['put','options']
    def put(self, request, tipo_id):
        data=TipoSerializer(data=request.data);data.is_valid(raise_exception=True)
        return Response(caso().catalogo(request.user.pk,data.validated_data,tipo_id))
