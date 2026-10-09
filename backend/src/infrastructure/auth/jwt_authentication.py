"""Rechaza identidades JWT antiguas o malformadas antes de consultar una PK UUID."""

from uuid import UUID

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.settings import api_settings


class UUIDJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            UUID(str(validated_token[api_settings.USER_ID_CLAIM]))
        except (KeyError, ValueError, TypeError, AttributeError) as error:
            raise InvalidToken('La sesión ya no es válida.') from error
        return super().get_user(validated_token)
