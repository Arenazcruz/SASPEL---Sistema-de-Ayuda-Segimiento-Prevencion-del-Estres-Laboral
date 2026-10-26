from django.utils import timezone
from src.domain.exceptions.superadmin import AdministrationError
from src.infrastructure.persistence.django.models import AsignacionInstrumento, InstrumentoPsicologico
from src.infrastructure.persistence.django.repositories.resultados import DjangoResultadosRepository
from src.infrastructure.persistence.django.repositories.responder_evaluacion import preguntas_disponibles
from src.application.services.evaluacion_configurada import contenido_disponible


class DjangoInstrumentAssignmentsRepository(DjangoResultadosRepository):
    def ahora(self):
        return timezone.now()

    @staticmethod
    def resumen(row):
        return {key: getattr(row, key) for key in ('id', 'instrumento_id', 'estado', 'fecha_asignacion', 'fecha_limite', 'asignado_por_id')} | {
            'nombre': row.instrumento.nombre, 'version': row.instrumento.version,
            'activo': row.instrumento.activo and not row.instrumento.deleted,
        }

    def listar(self, trabajador):
        return [self.resumen(row) for row in AsignacionInstrumento.objects.filter(
            trabajador_id=trabajador, deleted=False, instrumento__es_inicial=False,
        ).select_related('instrumento').order_by('-fecha_asignacion', '-pk')]

    def catalogo(self):
        return list(InstrumentoPsicologico.objects.filter(activo=True, deleted=False, es_inicial=False)
                    .order_by('nombre', 'version').values('id', 'nombre', 'version'))

    def asignar(self, actor, trabajador, instrumento, limite):
        row = InstrumentoPsicologico.objects.select_for_update().filter(pk=instrumento, activo=True, deleted=False, es_inicial=False).first()
        if row is None:
            raise AdministrationError('Selecciona un instrumento activo para seguimiento.')
        preguntas = preguntas_disponibles(row.pk)
        if not contenido_disponible(preguntas) or any(p.tipo_respuesta != 'ESCALA' for p in preguntas):
            raise AdministrationError('El instrumento no tiene una configuración de puntuación disponible.')
        if AsignacionInstrumento.objects.filter(trabajador_id=trabajador, instrumento=row, deleted=False, estado__in=['PENDIENTE', 'EN_PROGRESO']).exists():
            raise AdministrationError('El trabajador ya tiene una evaluación pendiente de esta versión.')
        assignment = AsignacionInstrumento.objects.create(trabajador_id=trabajador, instrumento=row,
            asignado_por_id=actor, origen='PROFESIONAL', fecha_limite=limite,
            creado_por=str(actor), actualizado_por=str(actor))
        return self.resumen(assignment)
