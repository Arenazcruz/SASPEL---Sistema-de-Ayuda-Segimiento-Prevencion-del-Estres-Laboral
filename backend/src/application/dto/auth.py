"""Datos que intercambian el proveedor de identidad, los casos de uso y las vistas de sesión. No
son tablas ni contienen dependencias de Django; los tokens se agregan en la vista.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LoginCommand:
    """Correo y clave recibidos para autenticar; password se excluye de repr, pero no se cifra
    dentro del DTO.
    """
    email: str
    password: str = field(repr=False)


@dataclass(frozen=True)
class AuthIdentity:
    """Cuenta verificada por el proveedor. groups conserva sus membresías; is_superuser participa
    en la resolución de SUPERADMIN.
    """
    id: int
    email: str
    first_name: str
    last_name: str
    groups: tuple[str, ...]
    is_superuser: bool


@dataclass(frozen=True)
class AuthenticatedUserDTO:
    """Identidad pública del login y me. role es el rol resuelto y dashboard_path la ruta Angular
    asociada; el formato final del login se arma en LoginView.
    """
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    dashboard_path: str
