from django.db.models.functions import Coalesce

from src.application.dto.resultados import MisTrabajadores, ResultadoResumen, TrabajadorAsignado
from src.domain.services.professional_assignment import WORKER_ROLES
from src.infrastructure.persistence.django.models import AsignacionProfesional, ResultadoInstrumento
from src.infrastructure.persistence.django.repositories.administration import DjangoAdministrationRepository


class DjangoResultadosRepository:
    def __init__(self):
        self.administration = DjangoAdministrationRepository()

    def atomic(self):
        # Comparte el bloqueo T23: una reasignación/cambio de rol no puede intercalarse
        # entre la autorización y la lectura de resultados de esta consulta.
        return self.administration.atomic()

    def usuarios(self):
        return self.administration.users().filter(is_active=True, deleted=False, perfil_usuario__deleted=False)

    def rol_activo(self, usuario_id):
        # Bootstrap administrativo válido sin perfil; perfiles borrados no autorizan.
        user = self.administration.users().filter(pk=usuario_id, is_active=True, deleted=False).exclude(
            perfil_usuario__deleted=True,
        ).first()
        if user is None:
            return None
        if user.functional_role in ('ADMIN', 'SUPERADMIN') or getattr(user, 'perfil_usuario', None) is not None:
            return user.functional_role
        return None

    def vinculos(self, psicologo_id):
        workers = self.usuarios().filter(functional_role__in=WORKER_ROLES).values('pk')
        return AsignacionProfesional.objects.filter(
            psicologo_id=psicologo_id, estado='ACTIVA', deleted=False, trabajador_id__in=workers,
        )

    def tiene_asignacion_activa(self, psicologo_id, trabajador_id):
        return self.vinculos(psicologo_id).filter(trabajador_id=trabajador_id).exists()

    def trabajadores(self, psicologo_id):
        rows = self.vinculos(psicologo_id).select_related(
            'trabajador__perfil_usuario__area', 'trabajador__perfil_usuario__cargo',
        ).order_by('trabajador__first_name', 'trabajador__last_name', 'trabajador__email', 'pk')
        workers = []
        for row in rows:
            user = row.trabajador
            profile = user.perfil_usuario
            name = ' '.join(filter(None, (user.first_name, user.last_name, profile.apellido_materno)))
            workers.append(TrabajadorAsignado(
                user.pk, name or user.email, user.email,
                profile.area.nombre if profile.area and not profile.area.deleted else '',
                profile.cargo.nombre if profile.cargo and not profile.cargo.deleted else '',
                row.fecha_asignacion, row.estado,
            ))
        return MisTrabajadores(len(workers), tuple(workers))

    @staticmethod
    def resultados():
        # No filtrar instrumento/rango por activo: las versiones retiradas siguen
        # describiendo el resultado original, sin reconstruir ni recalcular valores.
        return ResultadoInstrumento.objects.filter(
            deleted=False, aplicacion__deleted=False, aplicacion__estado='FINALIZADA',
            aplicacion__asignacion__deleted=False,
        ).select_related('aplicacion__asignacion__instrumento', 'rango').annotate(
            fecha_historial=Coalesce('aplicacion__fecha_finalizacion', 'fecha_calculo'),
        ).order_by('-fecha_historial', '-pk')

    @staticmethod
    def dto(row):
        instrument = row.aplicacion.asignacion.instrumento
        return ResultadoResumen(
            row.pk, instrument.nombre, instrument.version, row.fecha_historial,
            str(row.puntaje_total), row.rango.nombre if row.rango else None,
            row.rango.interpretacion if row.rango else '', row.aplicacion.estado,
        )

    def listar_resultados(self, trabajador_id):
        return tuple(self.dto(row) for row in self.resultados().filter(aplicacion__asignacion__trabajador_id=trabajador_id))

    def resultado(self, resultado_id):
        row = self.resultados().filter(pk=resultado_id).first()
        return (row.aplicacion.asignacion.trabajador_id, self.dto(row)) if row else None
