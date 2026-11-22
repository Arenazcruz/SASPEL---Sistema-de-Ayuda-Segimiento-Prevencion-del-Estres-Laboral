from src.infrastructure.persistence.django.models import Seguimiento
from src.infrastructure.persistence.django.models.recomendacion import Recomendacion
from src.infrastructure.persistence.django.repositories.resultados import DjangoResultadosRepository


class DjangoRecomendacionesRepository(DjangoResultadosRepository):
    def trabajador_seguimiento(self, pk):
        return Seguimiento.objects.filter(pk=pk, deleted=False).values_list('trabajador_id', flat=True).first()

    @staticmethod
    def dto(row):
        return {k: getattr(row, k) for k in ('id', 'seguimiento_id', 'profesional_id', 'texto', 'estado', 'creado_en', 'actualizado_en')}

    def listar(self, seguimiento):
        return [self.dto(r) for r in Recomendacion.objects.filter(seguimiento_id=seguimiento, deleted=False)]

    def compartidas(self, actor):
        return list(Recomendacion.objects.filter(compartida=True, deleted=False, seguimiento__deleted=False, seguimiento__trabajador_id=actor).values("id", "texto", "estado", "creado_en"))

    def crear(self, actor, seguimiento, texto, compartida):
        return self.dto(Recomendacion.objects.create(seguimiento_id=seguimiento, profesional_id=actor, texto=texto, compartida=compartida, creado_por=str(actor), actualizado_por=str(actor)))

    def obtener(self, seguimiento, recomendacion):
        row = Recomendacion.objects.select_for_update().filter(pk=recomendacion, seguimiento_id=seguimiento, deleted=False).first()
        return self.dto(row) if row else None

    def cambiar(self, actor, recomendacion, estado):
        row = Recomendacion.objects.get(pk=recomendacion)
        row.estado, row.actualizado_por = estado, str(actor)
        row.save(update_fields=['estado', 'actualizado_por'])
        return self.dto(row)
