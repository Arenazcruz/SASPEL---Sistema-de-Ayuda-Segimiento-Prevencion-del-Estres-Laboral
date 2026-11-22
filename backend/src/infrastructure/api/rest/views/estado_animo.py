from rest_framework import serializers
from rest_framework.response import Response
from src.infrastructure.api.rest.views.citas import CitasBaseView, EstrictoSerializer
from src.domain.entities.estado_animo import DatosAnimo
from src.application.use_cases.estado_animo import GestionarAnimo
from src.infrastructure.persistence.django.repositories.estado_animo import DjangoEstadoAnimoRepository

class AnimoSerializer(EstrictoSerializer):
    estado = serializers.CharField(max_length=100)
    intensidad = serializers.CharField(max_length=100)
    comentario = serializers.CharField(max_length=3000, required=False, allow_blank=True, default='')

class AnimoPropioView(CitasBaseView):
    http_method_names = ['get','post','head','options']
    def get(self, request):
        return Response(GestionarAnimo(DjangoEstadoAnimoRepository()).ejecutar(request.user.pk))
    def post(self, request):
        data=AnimoSerializer(data=request.data);data.is_valid(raise_exception=True)
        return Response(GestionarAnimo(DjangoEstadoAnimoRepository()).ejecutar(request.user.pk,datos=DatosAnimo(**data.validated_data)),status=201)

class AnimoProfesionalView(CitasBaseView):
    def get(self, request, trabajador_id):
        return Response(GestionarAnimo(DjangoEstadoAnimoRepository()).ejecutar(request.user.pk,trabajador_id))
