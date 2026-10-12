from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from src.application.services.auth_identity import MissingFunctionalRole
from src.infrastructure.dependencies.primer_acceso import build_primer_acceso


class PrimerAccesoCompleto(BasePermission):
    """Permiso común para las operaciones funcionales; auth tiene permisos explícitos propios."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            estado = build_primer_acceso().estado(request.user.pk)
        except MissingFunctionalRole:
            return False
        if not estado.completo:
            raise PermissionDenied({
                'code': 'primer_acceso_pendiente',
                'detail': 'Completa el primer acceso para continuar.',
                'siguiente_ruta': estado.siguiente_ruta,
            }, code='primer_acceso_pendiente')
        return True
