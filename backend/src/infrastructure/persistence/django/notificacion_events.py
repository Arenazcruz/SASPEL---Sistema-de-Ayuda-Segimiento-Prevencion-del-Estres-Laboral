from django.db.models.signals import post_save
from django.dispatch import receiver
from src.infrastructure.persistence.django.models import (Notificacion,Alerta,Cita,AsignacionProfesional,AsignacionInstrumento,ResultadoInstrumento,AplicacionInstrumento)
from src.infrastructure.persistence.django.repositories.resultados import DjangoResultadosRepository

def emitir(tipo,origen,evento,titulo,destinatarios):
    # Sin nombres, puntajes, observaciones ni contenido clínico en el resumen.
    for pk in set(destinatarios):
        Notificacion.objects.get_or_create(destinatario_id=pk,evento=f'{tipo}:{origen}:{evento}',defaults={'tipo':tipo,'titulo':titulo,'origen_id':origen})

@receiver(post_save,sender=Cita,dispatch_uid='saspel_notificacion_cita')
def cita(sender,instance,raw=False,**kwargs):
    if not raw and not instance.deleted:
        emitir('CITA',instance.pk,instance.estado,'Cita: '+instance.get_estado_display(),[instance.trabajador_id,instance.psicologo_id])

@receiver(post_save,sender=AsignacionProfesional,dispatch_uid='saspel_notificacion_asignacion')
def asignacion(sender,instance,raw=False,**kwargs):
    if not raw and not instance.deleted:
        emitir('ASIGNACION',instance.pk,instance.estado,'Asignación profesional: '+instance.get_estado_display(),[instance.trabajador_id,instance.psicologo_id])
        if instance.estado=='ACTIVA':
            for row in Alerta.objects.filter(deleted=False,estado__in=['ABIERTA','EN_ATENCION'],resultado__aplicacion__asignacion__trabajador_id=instance.trabajador_id):
                emitir('ALERTA',row.pk,'NUEVA','Alerta disponible para revisión',[instance.psicologo_id])

@receiver(post_save,sender=AsignacionInstrumento,dispatch_uid='saspel_notificacion_instrumento')
def instrumento(sender,instance,created=False,raw=False,**kwargs):
    if created and not raw and not instance.deleted:
        emitir('INSTRUMENTO',instance.pk,'ASIGNADO','Tienes un instrumento asignado',[instance.trabajador_id])

@receiver(post_save,sender=Alerta,dispatch_uid='saspel_notificacion_alerta')
def alerta(sender,instance,created=False,raw=False,**kwargs):
    if created and not raw and not instance.deleted:
        worker=instance.resultado.aplicacion.asignacion.trabajador_id
        ids=AsignacionProfesional.objects.filter(trabajador_id=worker,estado='ACTIVA',deleted=False).values_list('psicologo_id',flat=True)
        emitir('ALERTA',instance.pk,'NUEVA','Alerta disponible para revisión',ids)

def avisar_resultado(pk):
    row=DjangoResultadosRepository.resultados().filter(pk=pk).first()
    if row: emitir('RESULTADO',row.pk,'DISPONIBLE','Tu resultado está disponible',[row.aplicacion.asignacion.trabajador_id])

@receiver(post_save,sender=ResultadoInstrumento,dispatch_uid='saspel_notificacion_resultado')
def resultado(sender,instance,raw=False,**kwargs):
    if not raw: avisar_resultado(instance.pk)

@receiver(post_save,sender=AplicacionInstrumento,dispatch_uid='saspel_notificacion_finalizada')
def finalizada(sender,instance,raw=False,**kwargs):
    if not raw and instance.estado=='FINALIZADA':
        for pk in ResultadoInstrumento.objects.filter(aplicacion=instance,deleted=False).values_list('pk',flat=True): avisar_resultado(pk)
