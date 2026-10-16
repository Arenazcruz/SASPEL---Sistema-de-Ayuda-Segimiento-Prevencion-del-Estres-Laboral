import csv
import io
from django.http import HttpResponse
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from src.infrastructure.api.rest.views.citas import CitasBaseView,EstrictoSerializer
from src.application.use_cases.reportes import ConsultarReportes
from src.infrastructure.persistence.django.repositories.reportes import DjangoReportesRepository

class FiltrosReporte(EstrictoSerializer):
    desde=serializers.DateField(required=False)
    hasta=serializers.DateField(required=False)
    estado=serializers.CharField(required=False,max_length=100)
    area=serializers.UUIDField(required=False)
    instrumento=serializers.UUIDField(required=False)
    pagina=serializers.IntegerField(required=False,min_value=1,default=1)
    formato=serializers.ChoiceField(choices=['json','csv'],default='json')

def celda_csv(value):
    text='' if value is None else str(value)
    # Protege la apertura en planillas incluso si el campo comienza con espacios.
    return "'"+text if text.lstrip().startswith(('=','+','-','@')) or text.startswith(('\t','\r','\n')) else text

class ReportesView(CitasBaseView):
    def get(self,request,tipo):
        data=FiltrosReporte(data=request.query_params.dict());data.is_valid(raise_exception=True)
        filters=dict(data.validated_data);formato=filters.pop('formato')
        if tipo=='catalogos' and (formato!='json' or set(request.query_params)):
            raise ValidationError('El catálogo no admite filtros ni exportación.')
        result=ConsultarReportes(DjangoReportesRepository()).ejecutar(request.user.pk,tipo,filters,formato=='csv')
        if formato=='json': return Response(result)
        output=io.StringIO();writer=csv.writer(output);writer.writerow(result['columnas'])
        writer.writerows([[celda_csv(v) for v in row] for row in result['filas']])
        response=HttpResponse('\ufeff'+output.getvalue(),content_type='text/csv; charset=utf-8')
        response['Content-Disposition']=f'attachment; filename="saspel-{tipo}.csv"'
        return response
