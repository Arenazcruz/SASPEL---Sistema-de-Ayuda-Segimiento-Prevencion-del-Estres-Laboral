from rest_framework import serializers
from rest_framework.response import Response
from src.infrastructure.api.rest.views.citas import CitasBaseView,EstrictoSerializer
from src.application.use_cases.notificaciones import ConsultarNotificaciones
from src.infrastructure.persistence.django.repositories.notificaciones import DjangoNotificacionesRepository

def caso(): return ConsultarNotificaciones(DjangoNotificacionesRepository())

class FiltroNotificacion(EstrictoSerializer):
    pendientes=serializers.BooleanField(required=False,default=False)

class NotificacionesView(CitasBaseView):
    def get(self,request):
        data=FiltroNotificacion(data=request.query_params.dict());data.is_valid(raise_exception=True)
        return Response(caso().ejecutar(request.user.pk,solo_pendientes=data.validated_data['pendientes']))

class LeerNotificacionView(CitasBaseView):
    http_method_names=['post','options']
    def post(self,request,notificacion_id):
        data=EstrictoSerializer(data=request.data);data.is_valid(raise_exception=True)
        return Response(caso().ejecutar(request.user.pk,notificacion_id))
