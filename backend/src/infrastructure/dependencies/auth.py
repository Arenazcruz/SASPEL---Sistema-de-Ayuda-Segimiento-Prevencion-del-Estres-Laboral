"""Construye casos de sesión con DjangoAuthProvider. Es el punto para cambiar el proveedor
conservando los casos de Application.
"""

from src.application.ports.input.authentication import Authentication, CurrentIdentity
from src.application.use_cases.authenticate_user import AuthenticateUser
from src.application.use_cases.get_authenticated_user import GetAuthenticatedUser
from src.infrastructure.auth.django_auth_provider import DjangoAuthProvider


def build_authentication() -> Authentication:
    """Devuelve AuthenticateUser con proveedor Django; construirlo no autentica ni escribe datos."""
    return AuthenticateUser(DjangoAuthProvider())


def build_current_identity() -> CurrentIdentity:
    """Devuelve GetAuthenticatedUser con proveedor Django para resolver me."""
    return GetAuthenticatedUser(DjangoAuthProvider())
