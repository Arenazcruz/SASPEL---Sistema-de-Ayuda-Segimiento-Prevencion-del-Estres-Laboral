"""Superficie ADMIN de la institución única, sin ampliar /superadmin/.

Reutiliza contratos de catálogos/instrumentos/asignaciones. Las operaciones de
personas usan un repositorio acotado incluso al consultar IDs directamente.
El resumen se limita al personal; no publica cambio de roles.
"""
from django.urls import path
from rest_framework.permissions import BasePermission, IsAuthenticated
from src.infrastructure.api.rest.permissions import PrimerAccesoCompleto
from src.infrastructure.api.rest.superadmin_urls import urlpatterns as global_patterns
from src.infrastructure.persistence.django.repositories.institutional_administration import DjangoInstitutionalAdministrationRepository


class IsInstitutionAdmin(BasePermission):
    message = 'Esta función requiere administración institucional.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active
                    and request.user.groups.filter(name__in=['ADMIN', 'SUPERADMIN']).exists())


class InstitutionalAccess:
    permission_classes = [IsAuthenticated, PrimerAccesoCompleto, IsInstitutionAdmin]

    @staticmethod
    def build_administration(use_case):
        return use_case(DjangoInstitutionalAdministrationRepository())


urlpatterns = []
for pattern in global_patterns:
    if pattern.default_args.get('action') == 'role':
        continue
    original = pattern.callback.cls
    view = type('Institutional' + original.__name__, (InstitutionalAccess, original), {'__module__': __name__})
    urlpatterns.append(path(str(pattern.pattern), view.as_view(), pattern.default_args))
