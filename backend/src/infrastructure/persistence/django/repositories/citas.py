from django.db.models import Q
from django.utils import timezone

from src.domain.exceptions.resultados import ResultadoNoDisponible
from src.domain.exceptions.superadmin import AdministrationError
from src.domain.services.citas import validar_horario
from src.infrastructure.persistence.django.models import Cita, DisponibilidadPsicologo, AsignacionProfesional
from src.infrastructure.persistence.django.repositories.resultados import DjangoResultadosRepository


class DjangoCitasRepository(DjangoResultadosRepository):
    """Comparte el bloqueo de asignaciones para autorizar y reservar sin carreras."""
    @staticmethod
    def dto(cita):
        return {name: getattr(cita, name) for name in (
            'id', 'trabajador_id', 'psicologo_id', 'fecha_inicio', 'fecha_fin',
            'motivo', 'prioridad', 'estado', 'motivo_cierre', 'cita_origen_id',
        )} | {'trabajador': cita.trabajador.get_full_name() or cita.trabajador.email,
             'psicologo': cita.psicologo.get_full_name() or cita.psicologo.email}

    def filas(self):
        return Cita.objects.filter(deleted=False).select_related('trabajador', 'psicologo')

    def listar(self, actor, rol):
        rows = self.filas()
        if rol == 'TRABAJADOR':
            rows = rows.filter(trabajador_id=actor)
        else:
            rows = rows.filter(psicologo_id=actor, trabajador_id__in=self.vinculos(actor).values('trabajador_id'))
        return [self.dto(c) for c in rows.order_by('-fecha_inicio', '-pk')]

    def profesional(self, trabajador_id):
        eligible = self.usuarios().filter(functional_role='PSICOLOGO', perfil_usuario__habilitado_asignaciones=True)
        return AsignacionProfesional.objects.filter(
            trabajador_id=trabajador_id, estado='ACTIVA', deleted=False,
            psicologo_id__in=eligible.values('pk'),
        ).select_related('psicologo').first()

    def contexto(self, trabajador_id):
        link = self.profesional(trabajador_id)
        return {'psicologo': (link.psicologo.get_full_name() or link.psicologo.email) if link else None,
                'disponibilidad': self.disponibilidad(link.psicologo_id) if link else []}

    def disponibilidad(self, psicologo_id):
        return list(DisponibilidadPsicologo.objects.filter(psicologo_id=psicologo_id, activo=True, deleted=False)
                    .order_by('dia_semana', 'hora_inicio').values('id', 'dia_semana', 'hora_inicio', 'hora_fin'))

    def guardar_disponibilidad(self, actor, datos):
        if datos['hora_inicio'] >= datos['hora_fin']:
            raise AdministrationError('La hora de fin debe ser posterior a la de inicio.')
        rows = DisponibilidadPsicologo.objects.filter(psicologo_id=actor, dia_semana=datos['dia_semana'])
        exact = rows.filter(hora_inicio=datos['hora_inicio'], hora_fin=datos['hora_fin']).first()
        overlap = rows.filter(activo=True, deleted=False, hora_inicio__lt=datos['hora_fin'], hora_fin__gt=datos['hora_inicio'])
        if exact:
            overlap = overlap.exclude(pk=exact.pk)
        if overlap.exists():
            raise AdministrationError('El bloque se solapa con otro horario disponible.')
        row = exact or DisponibilidadPsicologo(psicologo_id=actor, creado_por=str(actor), **datos)
        row.activo, row.deleted, row.actualizado_por = True, False, str(actor)
        row.full_clean()
        row.save()

    def desactivar_disponibilidad(self, actor, bloque_id):
        row = DisponibilidadPsicologo.objects.filter(pk=bloque_id, psicologo_id=actor, deleted=False).first()
        if row is None:
            raise ResultadoNoDisponible('El horario no está disponible.')
        row.activo = False
        row.actualizado_por = str(actor)
        row.save(update_fields=['activo', 'actualizado_por'])

    def verificar_horario(self, psicologo_id, trabajador_id, inicio, fin, excluir=None):
        validar_horario(inicio, fin, timezone.now())
        local_inicio, local_fin = timezone.localtime(inicio), timezone.localtime(fin)
        if local_inicio.date() != local_fin.date() or not DisponibilidadPsicologo.objects.filter(
            psicologo_id=psicologo_id, activo=True, deleted=False,
            dia_semana=local_inicio.weekday(), hora_inicio__lte=local_inicio.time(), hora_fin__gte=local_fin.time(),
        ).exists():
            raise AdministrationError('El horario está fuera de la disponibilidad del profesional.')
        overlaps = Cita.objects.filter(deleted=False, estado='CONFIRMADA', fecha_inicio__lt=fin, fecha_fin__gt=inicio)
        if overlaps.filter(Q(psicologo_id=psicologo_id) | Q(trabajador_id=trabajador_id)).exclude(pk=excluir).exists():
            raise AdministrationError('El horario coincide con otra cita confirmada.')

    def solicitar(self, actor, datos):
        link = self.profesional(actor)
        if not link:
            raise AdministrationError('No tienes un psicólogo activo disponible en tu asignación.')
        self.verificar_horario(link.psicologo_id, actor, datos['fecha_inicio'], datos['fecha_fin'])
        if Cita.objects.filter(trabajador_id=actor, psicologo_id=link.psicologo_id, deleted=False,
                               estado='SOLICITADA', fecha_inicio=datos['fecha_inicio'], fecha_fin=datos['fecha_fin']).exists():
            raise AdministrationError('Ya tienes una solicitud para ese horario.')
        row = Cita(trabajador_id=actor, psicologo_id=link.psicologo_id, solicitada_por_id=actor,
                   creado_por=str(actor), actualizado_por=str(actor), **datos)
        row.full_clean()
        row.save()
        return self.dto(self.filas().get(pk=row.pk))

    def obtener(self, cita_id):
        row = self.filas().filter(pk=cita_id).first()
        return self.dto(row) if row else None

    def confirmar_horario(self, cita):
        self.verificar_horario(cita['psicologo_id'], cita['trabajador_id'], cita['fecha_inicio'], cita['fecha_fin'], cita['id'])

    def cambiar_estado(self, cita_id, estado, motivo, actor):
        row = self.filas().get(pk=cita_id)
        row.estado, row.motivo_cierre, row.actualizado_por = estado, motivo, str(actor)
        row.save(update_fields=['estado', 'motivo_cierre', 'actualizado_por'])
        return self.dto(row)
