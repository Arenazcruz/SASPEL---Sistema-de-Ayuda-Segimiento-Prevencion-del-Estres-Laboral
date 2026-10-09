"""Campos actuales de InstrumentoPsicologico. Estado y fechas no se editan en el formulario."""

from rest_framework import serializers
from src.infrastructure.api.rest.serializers.superadmin import StrictSerializer


class InstrumentRequestSerializer(StrictSerializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError({'non_field_errors': ['Se requiere un objeto JSON.']})
        return super().to_internal_value(data)


class InstrumentSerializer(InstrumentRequestSerializer):
    codigo = serializers.CharField(max_length=50)
    nombre = serializers.CharField(max_length=200)
    version = serializers.CharField(max_length=50, default='1.0')
    descripcion = serializers.CharField(allow_blank=True, required=False)
    instrucciones = serializers.CharField(allow_blank=True, required=False)
    es_inicial = serializers.BooleanField(required=False)


class InstrumentFilterSerializer(serializers.Serializer):
    search = serializers.CharField(max_length=200, allow_blank=True, required=False)
    activo = serializers.BooleanField(required=False)
    es_inicial = serializers.BooleanField(required=False)
    page = serializers.IntegerField(min_value=1, default=1)
