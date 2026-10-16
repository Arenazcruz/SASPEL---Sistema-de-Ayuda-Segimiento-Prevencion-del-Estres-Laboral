from django.db.models import Q
from django.utils import timezone
from src.infrastructure.persistence.django.models import Notificacion, Cita, AsignacionProfesional, AsignacionInstrumento
from src.infrastructure.persistence.django.repositories.alertas import DjangoAlertasRepository
from src.domain.exceptions.resultados import ResultadoNoDisponible

class DjangoNotificacionesRepository(DjangoAlertasRepository):
    def visibles(self,actor):
        role=self.rol_activo(actor)
        allowed=Q(pk__in=[])
        if role in ('ADMIN','SUPERADMIN'):
            allowed=Q(tipo='ASIGNACION_PENDIENTE')
        if role in ('TRABAJADOR','NUEVO_TRABAJADOR','PSICOLOGO'):
            workers=self.vinculos(actor).values('trabajador_id')
            citas=Cita.objects.filter(deleted=False)
            links=AsignacionProfesional.objects.filter(deleted=False)
            if role=='PSICOLOGO':
                citas=citas.filter(psicologo_id=actor,trabajador_id__in=workers)
                links=links.filter(psicologo_id=actor,estado='ACTIVA',trabajador_id__in=workers)
                allowed |= Q(tipo='ALERTA',origen_id__in=self.autorizadas(actor).values('pk'))
            else:
                citas=citas.filter(trabajador_id=actor)
                links=links.filter(trabajador_id=actor)
                allowed |= Q(tipo='RESULTADO',origen_id__in=self.resultados().filter(aplicacion__asignacion__trabajador_id=actor).values('pk'))
                allowed |= Q(tipo='INSTRUMENTO',origen_id__in=AsignacionInstrumento.objects.filter(trabajador_id=actor,deleted=False).values('pk'))
            allowed |= Q(tipo='CITA',origen_id__in=citas.values('pk')) | Q(tipo='ASIGNACION',origen_id__in=links.values('pk'))
        return Notificacion.objects.filter(allowed,destinatario_id=actor,deleted=False)

    def consultar(self,actor,notificacion=None,solo_pendientes=False):
        rows=self.visibles(actor)
        if notificacion is not None:
            row=rows.filter(pk=notificacion).first()
            if row is None: raise ResultadoNoDisponible('Notificación no disponible.')
            if row.leida_en is None:
                row.leida_en=timezone.now();row.actualizado_por=str(actor);row.save(update_fields=['leida_en','actualizado_por'])
            return {'id':row.pk,'leida_en':row.leida_en}
        if solo_pendientes: rows=rows.filter(leida_en__isnull=True)
        return list(rows.values('id','tipo','titulo','origen_id','creado_en','leida_en'))
