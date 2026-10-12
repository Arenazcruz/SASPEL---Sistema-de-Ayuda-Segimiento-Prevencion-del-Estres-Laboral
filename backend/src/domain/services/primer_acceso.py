ROLES_PASSWORD_TEMPORAL = frozenset({'NUEVO_TRABAJADOR', 'PSICOLOGO', 'ADMIN'})
ROLES_POLITICAS = ROLES_PASSWORD_TEMPORAL | {'TRABAJADOR'}


def requiere_password_temporal(role: str) -> bool:
    return role in ROLES_PASSWORD_TEMPORAL
