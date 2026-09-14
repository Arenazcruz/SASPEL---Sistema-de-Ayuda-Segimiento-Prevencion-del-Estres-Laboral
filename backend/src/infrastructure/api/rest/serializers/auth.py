"""Valida requests de login/refresh; no comprueba credenciales ni validez criptográfica."""

from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    """Acepta email y password sin recortar la clave; Application autentica."""
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=1024)


class RefreshSerializer(serializers.Serializer):
    """Acepta refresh sin recortarlo; JWTTokenProvider comprueba validez y vencimiento."""
    refresh = serializers.CharField(write_only=True, trim_whitespace=False, max_length=4096)
