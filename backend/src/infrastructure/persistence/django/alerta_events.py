from django.db.models.signals import post_save
from django.dispatch import receiver
from src.infrastructure.persistence.django.models import ResultadoInstrumento, AplicacionInstrumento
from src.application.use_cases.alertas import GestionarAlertas
from src.infrastructure.persistence.django.repositories.alertas import DjangoAlertasRepository

@receiver(post_save, sender=ResultadoInstrumento, dispatch_uid='saspel_alerta_resultado')
def resultado_guardado(sender, instance, raw=False, **kwargs):
    if not raw:
        GestionarAlertas(DjangoAlertasRepository()).generar(instance.pk)

@receiver(post_save, sender=AplicacionInstrumento, dispatch_uid='saspel_alerta_finalizada')
def aplicacion_finalizada(sender, instance, raw=False, **kwargs):
    if not raw and instance.estado == 'FINALIZADA':
        for pk in ResultadoInstrumento.objects.filter(aplicacion=instance,deleted=False).values_list('pk',flat=True):
            GestionarAlertas(DjangoAlertasRepository()).generar(pk)
