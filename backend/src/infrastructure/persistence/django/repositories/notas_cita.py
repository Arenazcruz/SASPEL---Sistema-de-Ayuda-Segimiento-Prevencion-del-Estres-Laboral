from src.infrastructure.persistence.django.repositories.citas import DjangoCitasRepository
from src.infrastructure.persistence.django.models import NotaCita

class DjangoNotasCitaRepository(DjangoCitasRepository):
    @staticmethod
    def nota_dto(row):
        return {'id':row.pk, 'cita_id':row.cita_id, 'profesional_id':row.profesional_id,
                'profesional':row.profesional.get_full_name() or row.profesional.email,
                'observacion':row.observacion, 'fecha':row.creado_en}

    def listar_notas(self, cita_id):
        return [self.nota_dto(row) for row in NotaCita.objects.filter(cita_id=cita_id, deleted=False).select_related('profesional')]

    def crear_nota(self, actor, cita_id, observacion):
        row = NotaCita.objects.create(cita_id=cita_id, profesional_id=actor, observacion=observacion,
                                      creado_por=str(actor), actualizado_por=str(actor))
        return self.nota_dto(row)
