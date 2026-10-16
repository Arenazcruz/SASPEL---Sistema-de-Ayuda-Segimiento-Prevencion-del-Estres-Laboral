from django.utils import timezone
from src.infrastructure.persistence.django.models import Cita,Seguimiento,EstadoAnimo,FactorPsicosocial,InstrumentoPsicologico,AsignacionProfesional
from src.infrastructure.persistence.django.repositories.notificaciones import DjangoNotificacionesRepository

class DjangoDashboardRepository(DjangoNotificacionesRepository):
    def indicadores(self,actor,rol):
        cards=[]
        def add(key,label,value): cards.append({'clave':key,'etiqueta':label,'valor':value})
        add('notificaciones','Notificaciones no leídas',self.visibles(actor).filter(leida_en__isnull=True).count())
        citas=Cita.objects.filter(deleted=False)
        if rol in ('ADMIN','SUPERADMIN'):
            users=self.usuarios()
            add('usuarios','Usuarios activos',users.count())
            add('trabajadores','Trabajadores activos',users.filter(functional_role__in=['TRABAJADOR','NUEVO_TRABAJADOR']).count())
            add('profesionales','Psicólogos activos',users.filter(functional_role='PSICOLOGO').count())
            add('instrumentos','Instrumentos activos',InstrumentoPsicologico.objects.filter(deleted=False,activo=True).count())
            add('asignaciones_pendientes','Trabajadores sin asignación',users.filter(functional_role__in=['TRABAJADOR','NUEVO_TRABAJADOR']).exclude(pk__in=AsignacionProfesional.objects.filter(deleted=False,estado='ACTIVA').values('trabajador_id')).count())
        elif rol=='PSICOLOGO':
            workers=self.vinculos(actor).values('trabajador_id')
            add('trabajadores','Trabajadores asignados',self.vinculos(actor).count())
            add('resultados','Resultados autorizados',self.resultados().filter(aplicacion__asignacion__trabajador_id__in=workers).count())
            add('seguimientos','Registros de seguimiento',Seguimiento.objects.filter(deleted=False,trabajador_id__in=workers).count())
            add('alertas','Alertas abiertas o en atención',self.autorizadas(actor).exclude(estado='CERRADA').count())
            citas=citas.filter(psicologo_id=actor,trabajador_id__in=workers)
        else:
            citas=citas.filter(trabajador_id=actor)
            add('resultados','Resultados disponibles',self.resultados().filter(aplicacion__asignacion__trabajador_id=actor).count())
            add('animo','Registros de ánimo',EstadoAnimo.objects.filter(deleted=False,trabajador_id=actor).count())
            add('factores','Factores registrados',FactorPsicosocial.objects.filter(deleted=False,trabajador_id=actor).count())
        add('citas_solicitadas','Citas solicitadas',citas.filter(estado='SOLICITADA').count())
        add('citas_proximas','Citas confirmadas por venir',citas.filter(estado='CONFIRMADA',fecha_inicio__gte=timezone.now()).count())
        return {'rol':rol,'indicadores':cards,'actualizado':timezone.now()}
