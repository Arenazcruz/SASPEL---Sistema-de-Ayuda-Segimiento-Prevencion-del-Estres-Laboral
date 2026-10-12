from rest_framework import serializers


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - self.fields.keys():
            raise serializers.ValidationError({'detail': 'La solicitud contiene campos no admitidos.'})
        return super().to_internal_value(data)


class StrictBooleanField(serializers.BooleanField):
    def to_internal_value(self, data):
        if type(data) is not bool:
            self.fail('invalid', input=data)
        return data


class StrictTextField(serializers.CharField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail('invalid')
        return super().to_internal_value(data)


class RespuestaEvaluacionSerializer(StrictSerializer):
    pregunta_id = serializers.UUIDField()
    opcion_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    valor_texto = StrictTextField(required=False, allow_null=True, allow_blank=True, default=None, max_length=20000)
    valor_numerico = serializers.DecimalField(max_digits=12, decimal_places=4, required=False, allow_null=True, default=None)
    valor_booleano = StrictBooleanField(required=False, allow_null=True, default=None)

    def validate(self, attrs):
        if attrs['valor_texto'] == '':
            attrs['valor_texto'] = None
        if attrs['valor_numerico'] is not None:
            attrs['valor_numerico'] = str(attrs['valor_numerico'])
        return attrs


class GuardarEvaluacionSerializer(StrictSerializer):
    respuestas = RespuestaEvaluacionSerializer(many=True, max_length=1000)


class IniciarEvaluacionSerializer(StrictSerializer):
    pass
