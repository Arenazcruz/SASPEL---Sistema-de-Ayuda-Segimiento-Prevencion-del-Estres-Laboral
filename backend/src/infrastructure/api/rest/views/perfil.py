from rest_framework import serializers
from rest_framework.response import Response
from src.application.use_cases.perfil import GestionarPerfilPropio
from src.infrastructure.api.rest.views.citas import CitasBaseView, EstrictoSerializer
from src.infrastructure.persistence.django.repositories.perfil import DjangoPerfilRepository


class PerfilSerializer(EstrictoSerializer):
    first_name=serializers.CharField(max_length=150,required=False)
    last_name=serializers.CharField(max_length=150,required=False)
    apellido_materno=serializers.CharField(max_length=150,allow_blank=True,required=False)
    telefono=serializers.CharField(max_length=15,allow_blank=True,required=False)
    fecha_nacimiento=serializers.DateField(allow_null=True,required=False)
    sexo=serializers.ChoiceField(choices=['','F','M','O'],required=False)


class PerfilPropioView(CitasBaseView):
    http_method_names=['get','patch','head','options']
    def get(self, request):
        return Response(GestionarPerfilPropio(DjangoPerfilRepository()).ejecutar(request.user.pk))
    def patch(self, request):
        data=PerfilSerializer(data=request.data);data.is_valid(raise_exception=True)
        return Response(GestionarPerfilPropio(DjangoPerfilRepository()).ejecutar(request.user.pk,data.validated_data))
