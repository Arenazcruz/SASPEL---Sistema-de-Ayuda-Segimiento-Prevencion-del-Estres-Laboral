"""Coordina las acciones de personas y catálogos del panel Superadmin. Las vistas validan HTTP y
permisos; estos casos aplican reglas y delegan los datos a AdministrationRepository.
Las escrituras usan atomic(): el adaptador Django revierte fallos y bloquea el grupo
SUPERADMIN para proteger las operaciones concurrentes. Cambiar aquí el flujo de registro, los
campos editables o las transiciones de rol; revisar serializers y formularios al cambiar esas
reglas.
"""

from dataclasses import replace
from src.application.dto.superadmin import CreateUserCommand, ResetPasswordCommand, UpdateUserCommand, UserFilters
from src.application.ports.output.administration import AdministrationRepository
from src.application.ports.input.administration import (
    DashboardOverview, PasswordReset, UserDetail, UserEdition, UserListing, UserRegistration,
)
from src.domain.exceptions.superadmin import AdministrationError
from src.domain.value_objects.functional_role import FunctionalRole

CREATION_ROLES = {role.value for role in FunctionalRole} - {'TRABAJADOR'}
ADMINISTRATIVE_ROLES = {'PSICOLOGO', 'ADMIN', 'SUPERADMIN'}
EDITABLE_FIELDS = {
    'email', 'first_name', 'last_name', 'apellido_materno', 'codigo_empleado',
    'nombre_preferido', 'fecha_nacimiento', 'sexo', 'telefono', 'area_id', 'cargo_id',
    'habilitado_asignaciones',
}


def validate_password(password: str, confirmation: str | None = None):
    """Valida longitud mínima de 8, al menos una letra y un número, y la confirmación si se
    recibe. No devuelve datos ni guarda claves; lanza AdministrationError asociado al campo.
    El repositorio aplica además los validadores Django; revisar password-validation.ts si
    cambia esta regla.
    """
    if len(password) < 8 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise AdministrationError('La contraseña requiere al menos 8 caracteres, una letra y un número.', 'password')
    if confirmation is not None and password != confirmation:
        raise AdministrationError('Las contraseñas no coinciden.', 'password_confirmation')


class UseCase:
    """Base que recibe el repositorio compartido por las operaciones administrativas."""
    def __init__(self, repository: AdministrationRepository):
        self.repository = repository


class ListUsers(UseCase, UserListing):
    """Sirve el listado del panel delegando búsqueda y paginación al repositorio."""
    def execute(self, filters: UserFilters):
        """Recibe UserFilters y devuelve UserPage, sin escrituras. Los filtros y tamaño de página
        se concretan en list_users del adaptador Django.
        """
        return self.repository.list_users(filters)


class GetUserDetail(UseCase, UserDetail):
    """Sirve la ficha de una persona al panel Superadmin."""
    def execute(self, user_id: int):
        """Recibe el ID de cuenta y devuelve UserDTO, incluso si falta perfil; propaga
        PersonNotFound si no existe.
        """
        return self.repository.get_user(user_id)


class CreateUser(UseCase, UserRegistration):
    """Registro desde Superadmin: valida rol y clave, normaliza correo y crea cuenta, perfil y
    grupo en una transacción. Requiere AdministrationRepository; no permite crear TRABAJADOR
    directamente.
    """
    def execute(self, command: CreateUserCommand):
        """Recibe CreateUserCommand y devuelve la persona creada. Admite NUEVO_TRABAJADOR,
        PSICOLOGO, ADMIN y SUPERADMIN. Los errores de validación o persistencia revierten el
        alta completa; la promoción de trabajadores pertenece a evaluación inicial, todavía no
        implementada.
        """
        if command.role not in CREATION_ROLES:
            raise AdministrationError('El rol TRABAJADOR se obtiene mediante la evaluación inicial.', 'role')
        validate_password(command.password)
        command = replace(command, email=command.email.strip().lower())
        with self.repository.atomic():
            return self.repository.create_user(command)


class UpdateUser(UseCase, UserEdition):
    """Edita datos personales desde la ficha; rol, estado y contraseña tienen acciones separadas."""
    def execute(self, command: UpdateUserCommand):
        """Recibe ID y cambios parciales en UpdateUserCommand; devuelve la ficha actualizada.
        Normaliza correo y solo permite habilitado_asignaciones a psicólogos. Rechaza campos
        ajenos a EDITABLE_FIELDS y revierte la escritura si falla el repositorio.
        """
        if set(command.changes) - EDITABLE_FIELDS:
            raise AdministrationError('Utiliza las acciones específicas para cambiar rol, estado o contraseña.')
        changes = dict(command.changes)
        if 'email' in changes:
            changes['email'] = changes['email'].strip().lower()
        with self.repository.atomic():
            user = self.repository.get_user(command.user_id)
            if 'habilitado_asignaciones' in changes and user.role != 'PSICOLOGO':
                raise AdministrationError('Esta opción solo corresponde a psicólogos.', 'habilitado_asignaciones')
            return self.repository.update_user(command.user_id, changes)


def protect_superadmin(repository, user, actor_id):
    """Recibe repositorio, ficha afectada y actor_id (quien solicita el cambio). Rechaza quitarse
    acceso a sí mismo o afectar al último SUPERADMIN activo. No escribe; debe ejecutarse
    dentro de atomic() para mantener la protección ante solicitudes simultáneas.
    """
    if user.role != 'SUPERADMIN':
        return
    if user.id == actor_id:
        raise AdministrationError('No puedes desactivarte ni quitarte tu propio rol SUPERADMIN.')
    if user.is_active and repository.active_superadmins() <= 1:
        raise AdministrationError('Debe permanecer al menos un SUPERADMIN activo.')


class DeactivateUser(UseCase):
    """Desactiva acceso desde Superadmin conservando la persona y su historial."""
    def execute(self, user_id: int, actor_id: int):
        """Recibe ID objetivo y actor; protege el acceso administrativo y devuelve la ficha
        inactiva. La cuenta deja de pasar login y renovación JWT. El bloqueo y la escritura
        comparten transacción.
        """
        with self.repository.atomic():
            user = self.repository.get_user(user_id)
            protect_superadmin(self.repository, user, actor_id)
            return self.repository.set_active(user_id, False)


class ActivateUser(UseCase):
    """Rehabilita una cuenta existente desde el panel administrativo."""
    def execute(self, user_id: int):
        """Recibe ID y devuelve la ficha con is_active=True dentro de una transacción; no cambia
        rol ni habilitado_asignaciones.
        """
        with self.repository.atomic():
            return self.repository.set_active(user_id, True)


class ChangeUserRole(UseCase):
    """Corrige roles desde el panel y protege el acceso de los Superadmin. El repositorio
    sincroniza grupo, flags Django y datos del perfil.
    """
    def execute(self, user_id: int, role: str, actor_id: int):
        """Recibe ID, rol destino y actor. Devuelve la ficha sin escribir si el rol es el mismo;
        para cambios exige un origen PSICOLOGO, ADMIN o SUPERADMIN y un destino de
        CREATION_ROLES. Protege al actor y al último Superadmin; cualquier fallo revierte la
        operación.
        """
        with self.repository.atomic():
            user = self.repository.get_user(user_id)
            if role == user.role:
                return user
            if role not in CREATION_ROLES or user.role not in ADMINISTRATIVE_ROLES:
                raise AdministrationError('Solo se permiten correcciones desde roles administrativos; la transición de trabajadores pertenece a evaluación inicial.', 'role')
            protect_superadmin(self.repository, user, actor_id)
            return self.repository.set_role(user_id, role)


class ResetUserPassword(UseCase, PasswordReset):
    """Restablece la clave de una persona desde la acción administrativa dedicada."""
    def execute(self, command: ResetPasswordCommand):
        """Recibe ID, contraseña y confirmación; valida y persiste el hash mediante el
        repositorio. Devuelve None y propaga errores por campo. No ejecuta una revocación de
        tokens existentes.
        """
        validate_password(command.password, command.password_confirmation)
        with self.repository.atomic():
            self.repository.reset_password(command.user_id, command.password)


class GetSuperadminDashboardSummary(UseCase, DashboardOverview):
    """Obtiene las estadísticas reales que muestra el inicio de Superadmin."""
    def execute(self):
        """Devuelve DashboardSummary con totales y personas recientes; no escribe. Los criterios
        y límite de recientes se cambian en summary del repositorio.
        """
        return self.repository.summary()


class ManageInstitution(UseCase):
    """Gestiona áreas y cargos para las pantallas institucionales mediante
    AdministrationRepository. Desactivar conserva los vínculos históricos.
    """
    def list(self, kind: str, active: bool | None = None):
        """Recibe kind (areas o cargos) y active; None incluye ambos estados. Devuelve DTO
        ordenados por el repositorio, sin escrituras.
        """
        return self.repository.list_institution(kind, active)

    def get(self, kind: str, item_id: int):
        """Recibe kind e ID; devuelve InstitutionDTO o propaga PersonNotFound."""
        return self.repository.get_institution(kind, item_id)

    def save(self, kind: str, item_id: int | None, changes: dict):
        """Recibe kind, ID (None para crear) y cambios de nombre/descripcion. Devuelve el
        catálogo guardado en una transacción; rechaza otros campos. El estado solo se cambia
        por la acción dedicada.
        """
        if set(changes) - {'nombre', 'descripcion'}:
            raise AdministrationError('Utiliza activar o desactivar para modificar el estado.')
        with self.repository.atomic():
            return self.repository.save_institution(kind, item_id, changes)

    def set_active(self, kind: str, item_id: int, active: bool):
        """Recibe kind, ID y estado; devuelve el registro actualizado. Conserva perfiles
        asociados y revierte ante errores del repositorio.
        """
        with self.repository.atomic():
            return self.repository.save_institution(kind, item_id, {'activo': active})
