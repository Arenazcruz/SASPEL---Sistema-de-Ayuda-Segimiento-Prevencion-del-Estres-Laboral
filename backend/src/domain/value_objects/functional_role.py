"""Define los cinco roles de SASPEL que comparten autenticación y administración. Para añadir
uno, revisar la prioridad de auth_identity, los grupos de BD, permisos, serializers y
ROLE_DASHBOARDS/ROLE_LABELS del frontend.
"""

from enum import StrEnum


class FunctionalRole(StrEnum):
    """Nombres persistidos en grupos y enviados por API; cambiarlos afecta acceso y navegación."""
    NUEVO_TRABAJADOR = 'NUEVO_TRABAJADOR'
    TRABAJADOR = 'TRABAJADOR'
    PSICOLOGO = 'PSICOLOGO'
    ADMIN = 'ADMIN'
    SUPERADMIN = 'SUPERADMIN'
