from rest_framework import serializers
from rest_framework.response import Response
from src.infrastructure.api.rest.views.citas import CitasBaseView, EstrictoSerializer
from src.application.use_cases.alertas import GestionarAlertas
from src.infrastructure.persistence.django.repositories.alertas import DjangoAlertasRepository

def caso(): return GestionarAlertas(DjangoAlertasRepository())

class ReglaSerializer(EstrictoSerializer):
    nombre=serializers.CharField(max_length=150)
    rango_id=serializers.UUIDField()
    nivel=serializers.ChoiceField(choices=['BAJA','MEDIA','ALTA'])

class AccionAlertaSerializer(EstrictoSerializer):
    estado=serializers.ChoiceField(choices=['EN_ATENCION','CERRADA'])
    observacion=serializers.CharField(max_length=5000)

class ReglasAlertaView(CitasBaseView):
    http_method_names=['get','post','head','options']
    def get(self,request): return Response(caso().reglas(request.user.pk))
    def post(self,request):
        data=ReglaSerializer(data=request.data);data.is_valid(raise_exception=True)
        return Response(caso().reglas(request.user.pk,data.validated_data),status=201)

class DesactivarReglaView(CitasBaseView):
    http_method_names=['post','options']
    def post(self,request,regla_id):
        data=EstrictoSerializer(data=request.data);data.is_valid(raise_exception=True)
        return Response(caso().reglas(request.user.pk,regla=regla_id))

class AlertasView(CitasBaseView):
    def get(self,request): return Response(caso().consultar(request.user.pk))

class AccionAlertaView(CitasBaseView):
    http_method_names=['post','options']
    def post(self,request,alerta_id):
        data=AccionAlertaSerializer(data=request.data);data.is_valid(raise_exception=True)
        return Response(caso().consultar(request.user.pk,alerta_id,data.validated_data))
