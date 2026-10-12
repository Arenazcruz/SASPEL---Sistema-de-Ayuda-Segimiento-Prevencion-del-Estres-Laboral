from contextlib import contextmanager

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from src.application.dto.primer_acceso import CuentaPrimerAcceso, PoliticaDTO
from src.application.services.auth_identity import present_identity
from src.domain.exceptions.primer_acceso import PrimerAccesoError
from src.infrastructure.auth.django_auth_provider import DjangoAuthProvider
from src.infrastructure.persistence.django.models import AceptacionPolitica, PoliticaSistema


class DjangoPrimerAccesoRepository:
    def __init__(self):
        self._locked = False

    @contextmanager
    def atomic(self, usuario_id):
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=usuario_id)
            self._locked = True
            try:
                yield
            finally:
                self._locked = False

    def cuenta(self, usuario_id):
        user = get_user_model().objects.get(pk=usuario_id)
        identity = present_identity(DjangoAuthProvider._identity(user))
        return CuentaPrimerAcceso(identity.role, identity.dashboard_path, user.debe_cambiar_password)

    def ahora(self):
        return timezone.now()

    def politicas(self):
        query = PoliticaSistema.objects.filter(deleted=False)
        if self._locked:
            query = query.select_for_update()
        return [PoliticaDTO(p.pk, p.tipo, p.titulo, p.version, p.contenido,
                            p.vigente_desde, p.obligatoria, p.activo) for p in query]

    def aceptadas(self, usuario_id):
        return set(AceptacionPolitica.objects.filter(usuario_id=usuario_id).values_list('politica_id', flat=True))

    def cambiar_password(self, usuario_id, password):
        user = get_user_model().objects.get(pk=usuario_id)
        if user.check_password(password):
            raise PrimerAccesoError('La nueva contraseña debe ser diferente de la temporal.', 'password')
        try:
            validate_password(password, user)
        except ValidationError as error:
            raise PrimerAccesoError(' '.join(error.messages), 'password') from None
        user.set_password(password)
        user.debe_cambiar_password = False
        user.actualizado_por = str(usuario_id)
        user.save(update_fields=['password', 'debe_cambiar_password', 'actualizado_por'])

    def aceptar(self, usuario_id, politicas):
        for politica_id in sorted(politicas):
            AceptacionPolitica.objects.get_or_create(
                usuario_id=usuario_id, politica_id=politica_id,
                defaults={'creado_por': str(usuario_id), 'actualizado_por': str(usuario_id)},
            )
