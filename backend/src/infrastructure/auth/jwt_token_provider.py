"""Emite y renueva JWT mediante SimpleJWT para las vistas de sesión. Las duraciones se configuran
en config/settings.py; actualmente no hay blacklist ni rotación del refresh.
"""

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken


class JWTTokenProvider:
    """Responsable técnico de tokens; exige cuenta activa pero no resuelve roles funcionales."""
    @staticmethod
    def issue(user_id: int) -> dict[str, str]:
        """Recibe ID y devuelve access/refresh para una cuenta activa. Sin cuenta válida lanza
        InvalidToken. No guarda una sesión adicional; el login debe resolver el rol antes de
        invocarlo.
        """
        user = get_user_model().objects.filter(pk=user_id, is_active=True).first()
        if user is None:
            raise InvalidToken('No se pudo iniciar la sesión.')
        refresh = RefreshToken.for_user(user)
        return {'access': str(refresh.access_token), 'refresh': str(refresh)}

    @staticmethod
    def renew(raw_token: str) -> dict[str, str]:
        """Recibe refresh serializado y devuelve solo un nuevo access. Verifica token y que la
        cuenta siga activa; traduce expiración/formato inválido a InvalidToken. No rota
        refresh ni consulta rol: me y los permisos consultan la cuenta vigente.
        """
        try:
            refresh = RefreshToken(raw_token)
            user_id = refresh[api_settings.USER_ID_CLAIM]
            # Una cuenta borrada o desactivada tampoco puede renovar su sesión.
            if not get_user_model().objects.filter(pk=user_id, is_active=True).exists():
                raise InvalidToken('La sesión ya no es válida.')
            return {'access': str(refresh.access_token)}
        except (TokenError, KeyError, ValueError, TypeError, OverflowError) as error:
            raise InvalidToken('La sesión expiró o no es válida.') from error
