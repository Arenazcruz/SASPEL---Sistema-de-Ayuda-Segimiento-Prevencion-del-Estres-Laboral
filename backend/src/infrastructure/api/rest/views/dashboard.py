from rest_framework.response import Response
from src.infrastructure.api.rest.views.citas import CitasBaseView,EstrictoSerializer
from src.application.use_cases.dashboard import ConsultarDashboard
from src.infrastructure.persistence.django.repositories.dashboard import DjangoDashboardRepository

class DashboardView(CitasBaseView):
    def get(self,request):
        data=EstrictoSerializer(data=request.query_params.dict());data.is_valid(raise_exception=True)
        return Response(ConsultarDashboard(DjangoDashboardRepository()).ejecutar(request.user.pk))
