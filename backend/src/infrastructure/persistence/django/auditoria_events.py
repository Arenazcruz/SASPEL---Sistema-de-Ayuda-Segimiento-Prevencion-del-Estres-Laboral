from contextvars import ContextVar
from uuid import UUID
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models.auditable import AuditableModel
from .models.evento_auditoria import EventoAuditoria

solicitud_actual = ContextVar('saspel_solicitud_auditoria', default=None)


def actor_actual(instance=None):
    request = solicitud_actual.get()
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        return user.pk
    try:
        pk = UUID(getattr(instance, 'actualizado_por', 'SYSTEM'))
    except (ValueError, TypeError, AttributeError):
        return None
    return pk if get_user_model().objects.filter(pk=pk).exists() else None


@receiver(post_save, dispatch_uid='saspel_auditoria_modelos')
def registrar_cambio(sender, instance, created=False, raw=False, **kwargs):
    if raw or not isinstance(instance, AuditableModel) or sender._meta.model_name == 'notificacion':
        return
    # Solo estados de catálogos cerrados. El estado libre de un seguimiento no se registra.
    estado = getattr(instance, 'estado', '') if sender._meta.model_name in {
        'cita', 'asignacionprofesional', 'asignacioninstrumento', 'aplicacioninstrumento', 'recomendacion', 'alerta',
    } else ''
    EventoAuditoria.objects.create(actor_id=actor_actual(instance), accion='CREAR' if created else 'ACTUALIZAR',
        entidad=sender._meta.model_name, entidad_id=instance.pk, estado=estado)


class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = solicitud_actual.set(request)
        try:
            response = self.get_response(request)
            match = request.resolver_match
            actor = actor_actual()
            # La consulta de auditoría no se registra a sí misma. No se guardan
            # query strings, cuerpos, nombres, puntajes ni textos de respuestas.
            if actor and match and request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and request.path.startswith('/api/') and '/auditoria/' not in request.path and 200 <= response.status_code < 300:
                ids = [value for value in match.kwargs.values() if isinstance(value, UUID)]
                EventoAuditoria.objects.create(actor_id=actor, accion=request.method,
                    entidad=match.route[:200], entidad_id=ids[-1] if ids else None)
            return response
        finally:
            solicitud_actual.reset(token)
