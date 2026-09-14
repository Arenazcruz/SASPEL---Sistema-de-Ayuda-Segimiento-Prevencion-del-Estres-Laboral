"""Conecta el login por correo con las cuentas, hash y grupos de Django. Revisar aquí búsquedas y
comprobación de actividad; la prioridad de roles está en Application y la emisión JWT en
jwt_token_provider.py.
"""

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from src.application.dto.auth import AuthIdentity
from src.application.services.auth_identity import InactiveAccount, InvalidCredentials


class DjangoAuthProvider:
    """Implementa AuthProvider sobre User y sus grupos; devuelve DTO sin exponer modelos a
    Application.
    """
    def authenticate(self, email: str, password: str) -> AuthIdentity:
        """Busca correo sin distinguir mayúsculas y exige exactamente una cuenta. Verifica clave
        y actividad, actualiza last_login y devuelve AuthIdentity. Duplicados o clave
        incorrecta producen InvalidCredentials; solo una clave correcta revela
        InactiveAccount.
        """
        User = get_user_model()
        candidates = list(User.objects.filter(email__iexact=email.strip())[:2])
        # Django permite correos repetidos. Si hay ambigüedad no elegimos una
        # cuenta arbitrariamente ni revelamos cuántas existen.
        if len(candidates) != 1:
            make_password(password)
            raise InvalidCredentials()
        user = candidates[0]
        if not user.is_active:
            # Solo distinguimos una cuenta inactiva después de verificar su clave.
            if check_password(password, user.password):
                raise InactiveAccount()
            raise InvalidCredentials()
        verified = authenticate(username=user.get_username(), password=password)
        if verified is None or verified.pk != user.pk:
            raise InvalidCredentials()
        # El login propio no utiliza la vista de SimpleJWT que actualiza este dato.
        User.objects.filter(pk=verified.pk).update(last_login=timezone.now())
        return self._identity(verified)

    def get_identity(self, user_id: int) -> AuthIdentity:
        """Busca ID de cuenta y devuelve identidad con grupos actuales. Lanza InvalidCredentials
        si falta e InactiveAccount si está desactivada; no modifica datos.
        """
        user = get_user_model().objects.filter(pk=user_id).first()
        if user is None:
            raise InvalidCredentials()
        if not user.is_active:
            raise InactiveAccount()
        return self._identity(user)

    @staticmethod
    def _identity(user) -> AuthIdentity:
        """Convierte una cuenta Django en AuthIdentity y consulta sus grupos. Conserva
        is_superuser para la prioridad de roles de Application.
        """
        return AuthIdentity(
            id=user.pk, email=user.email,
            first_name=user.first_name, last_name=user.last_name,
            groups=tuple(user.groups.values_list('name', flat=True)),
            is_superuser=user.is_superuser,
        )
