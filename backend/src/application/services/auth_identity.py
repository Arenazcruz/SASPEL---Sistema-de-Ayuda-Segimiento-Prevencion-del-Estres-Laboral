"""Resuelve el rol funcional y la dirección del panel que devuelven login y me. ROLE_DASHBOARDS
también determina el rol mostrado y contado por el repositorio administrativo. Si cambia un
rol o su ruta, revisar functional_role.py, auth.models.ts y los guards/rutas Angular.
"""

from src.application.dto.auth import AuthenticatedUserDTO, AuthIdentity
from src.domain.value_objects.functional_role import FunctionalRole


class InvalidCredentials(Exception):
    """El correo y la contraseña no permiten iniciar sesión."""


class InactiveAccount(Exception):
    """La cuenta tiene credenciales válidas, pero está desactivada."""


class MissingFunctionalRole(Exception):
    """La cuenta aún no tiene un rol que permita acceder a un panel."""


# Si hay varios grupos, prevalece el primero de esta lista. El registro y cambio
# de rol administrativos ya fijan un solo grupo; esta prioridad cubre cuentas previas.
ROLE_DASHBOARDS = {
    FunctionalRole.SUPERADMIN: '/dashboard/superadmin',
    FunctionalRole.ADMIN: '/dashboard/admin',
    FunctionalRole.PSICOLOGO: '/dashboard/psicologo',
    FunctionalRole.TRABAJADOR: '/dashboard/trabajador',
    FunctionalRole.NUEVO_TRABAJADOR: '/dashboard/nuevo-trabajador',
}


def present_identity(identity: AuthIdentity) -> AuthenticatedUserDTO:
    """Recibe AuthIdentity verificada y devuelve AuthenticatedUserDTO. Prioriza SUPERADMIN,
    ADMIN, PSICOLOGO, TRABAJADOR y NUEVO_TRABAJADOR, en ese orden; is_superuser añade
    SUPERADMIN. No escribe ni comprueba actividad: lo hace el proveedor. Sin rol conocido
    lanza MissingFunctionalRole.
    """
    roles = set(identity.groups)
    if identity.is_superuser:
        roles.add(FunctionalRole.SUPERADMIN)
    for role, path in ROLE_DASHBOARDS.items():
        if role in roles:
            return AuthenticatedUserDTO(
                id=identity.id, email=identity.email,
                first_name=identity.first_name, last_name=identity.last_name,
                role=role.value, dashboard_path=path,
            )
    raise MissingFunctionalRole()
