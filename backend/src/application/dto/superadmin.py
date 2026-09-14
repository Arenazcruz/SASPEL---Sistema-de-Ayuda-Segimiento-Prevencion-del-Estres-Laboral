"""Entradas y resultados de la administración de personas y catálogos. Transportan datos entre
casos de uso y repositorio sin depender de HTTP ni representar tablas. Las salidas nunca
contienen claves.
"""

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class CreateUserCommand:
    """Datos para dar de alta cuenta, perfil y rol desde Superadmin. area_id/cargo_id son
    referencias opcionales; habilitado_asignaciones solo se conserva para PSICOLOGO.
    """
    email: str
    password: str = field(repr=False)
    first_name: str
    last_name: str
    apellido_materno: str
    codigo_empleado: str
    role: str
    nombre_preferido: str = ''
    fecha_nacimiento: date | None = None
    sexo: str = ''
    telefono: str = ''
    area_id: int | None = None
    cargo_id: int | None = None
    habilitado_asignaciones: bool = True


@dataclass(frozen=True)
class UpdateUserCommand:
    """ID de cuenta y diccionario de campos presentes en una edición parcial; omitir un campo
    conserva su valor. No transporta cambios de rol, estado o contraseña.
    """
    user_id: int
    changes: dict


@dataclass(frozen=True)
class ResetPasswordCommand:
    """ID objetivo y clave con confirmación para el restablecimiento. Ambas claves se omiten de
    repr, pero siguen en memoria hasta terminar la operación.
    """
    user_id: int
    password: str = field(repr=False)
    password_confirmation: str = field(repr=False)


@dataclass(frozen=True)
class UserFilters:
    """Filtros del listado: search busca correo, nombres, apellidos paternos o código;
    active=None incluye ambos estados. area/cargo son IDs y page comienza en 1.
    """
    search: str = ''
    role: str = ''
    active: bool | None = None
    area: int | None = None
    cargo: int | None = None
    page: int = 1


@dataclass(frozen=True)
class InstitutionDTO:
    """Área o cargo para listados y fichas; activo permite conservar referencias retiradas del
    catálogo seleccionable.
    """
    id: int
    nombre: str
    descripcion: str
    activo: bool


@dataclass(frozen=True)
class UserDTO:
    """Ficha administrativa de cuenta y perfil, sin contraseña. role puede ser None en cuentas
    sin rol; tiene_perfil distingue un perfil ausente de campos opcionales vacíos.
    tamizaje_resuelto marca evaluación inicial y habilitado_asignaciones la recepción de
    trabajadores, no el acceso a la cuenta.
    """
    id: int
    email: str
    first_name: str
    last_name: str
    nombre_completo: str
    role: str | None
    is_active: bool
    fecha_registro: datetime
    last_login: datetime | None
    codigo_empleado: str = ''
    apellido_materno: str = ''
    nombre_preferido: str = ''
    fecha_nacimiento: date | None = None
    sexo: str = ''
    telefono: str = ''
    area: InstitutionDTO | None = None
    cargo: InstitutionDTO | None = None
    tamizaje_resuelto: bool = False
    habilitado_asignaciones: bool = False
    tiene_perfil: bool = False


@dataclass(frozen=True)
class UserPage:
    """Página de personas: count cuenta todos los resultados filtrados; page/page_size describen
    el tramo incluido en results.
    """
    count: int
    page: int
    page_size: int
    results: list[UserDTO]


@dataclass(frozen=True)
class DashboardSummary:
    """Totales de cuentas por rol/estado y cinco registros recientes calculados por el
    repositorio; Angular solo los presenta.
    """
    users_total: int
    new_workers: int
    workers: int
    psychologists: int
    admins: int
    superadmins: int
    active_users: int
    inactive_users: int
    recent_users: list[UserDTO]
