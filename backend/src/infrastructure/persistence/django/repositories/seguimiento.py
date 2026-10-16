from dataclasses import asdict
from django.utils import timezone
from src.infrastructure.persistence.django.models import Seguimiento
from src.infrastructure.persistence.django.repositories.resultados import DjangoResultadosRepository

class DjangoSeguimientoRepository(DjangoResultadosRepository):
    def hoy(self):
        return timezone.localdate()

    @staticmethod
    def dto(row):
        return {key:getattr(row,key) for key in ('id','trabajador_id','profesional_id','motivo','categoria',
                'observacion','estado','evolucion','plan_accion','proxima_revision')} | {
                'fecha':row.creado_en, 'profesional':row.profesional.get_full_name() or row.profesional.email}

    def historial(self, trabajador):
        user = self.usuarios().get(pk=trabajador)
        rows = Seguimiento.objects.filter(trabajador_id=trabajador,deleted=False).select_related('profesional')
        return {'trabajador':user.get_full_name() or user.email, 'registros':[self.dto(row) for row in rows]}

    def registrar(self, actor, trabajador, datos):
        row = Seguimiento.objects.create(trabajador_id=trabajador,profesional_id=actor,
                creado_por=str(actor),actualizado_por=str(actor),**asdict(datos))
        return self.dto(row)
