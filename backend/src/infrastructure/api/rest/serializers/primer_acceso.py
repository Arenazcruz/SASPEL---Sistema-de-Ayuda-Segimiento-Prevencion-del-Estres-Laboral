from rest_framework import serializers

from src.infrastructure.api.rest.serializers.superadmin import PasswordSerializer, StrictSerializer


class CambiarPasswordSerializer(PasswordSerializer):
    pass


class AceptarPoliticasSerializer(StrictSerializer):
    politicas = serializers.ListField(child=serializers.UUIDField(), allow_empty=False, max_length=3)
