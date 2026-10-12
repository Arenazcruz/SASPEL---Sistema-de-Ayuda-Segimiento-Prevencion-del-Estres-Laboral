from src.application.dto.nuevo_trabajador import EvaluacionInicialDTO
from src.infrastructure.persistence.django.models import AsignacionInstrumento


class DjangoNuevoTrabajadorRepository:
    def evaluacion_inicial(self, usuario_id):
        # La asignación inicial más reciente no cancelada define el resumen.
        # Las versiones inactivas conservan su historial; se excluyen borrados lógicos.
        asignacion = (
            AsignacionInstrumento.objects.select_related('instrumento')
            .filter(trabajador_id=usuario_id, deleted=False,
                    instrumento__es_inicial=True, instrumento__deleted=False,
                    estado__in=['PENDIENTE', 'EN_PROGRESO', 'COMPLETADA'])
            .order_by('-fecha_asignacion', '-pk').first()
        )
        if asignacion is None:
            return None
        return EvaluacionInicialDTO(
            estado=asignacion.estado, asignacion_id=asignacion.pk,
            instrumento_id=asignacion.instrumento_id, nombre=asignacion.instrumento.nombre,
            version=asignacion.instrumento.version,
            fecha_asignacion=asignacion.fecha_asignacion, fecha_limite=asignacion.fecha_limite,
        )
