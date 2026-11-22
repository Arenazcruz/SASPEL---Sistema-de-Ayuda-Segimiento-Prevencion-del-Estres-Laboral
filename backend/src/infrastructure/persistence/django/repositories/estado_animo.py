from dataclasses import asdict
from src.infrastructure.persistence.django.models import EstadoAnimo
from src.infrastructure.persistence.django.repositories.resultados import DjangoResultadosRepository

class DjangoEstadoAnimoRepository(DjangoResultadosRepository):
    @staticmethod
    def dto(row):
        return {'id':row.pk,'estado':row.estado,'intensidad':row.intensidad,'comentario':row.comentario,'fecha':row.creado_en}

    def historial(self, trabajador):
        user = self.usuarios().get(pk=trabajador)
        rows = EstadoAnimo.objects.filter(trabajador_id=trabajador,deleted=False)
        return {'trabajador':user.get_full_name() or user.email,'registros':[self.dto(row) for row in rows]}

    def registrar(self, trabajador, datos):
        row = EstadoAnimo.objects.create(trabajador_id=trabajador,creado_por=str(trabajador),actualizado_por=str(trabajador),**asdict(datos))
        return self.dto(row)
