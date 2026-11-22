from rest_framework import serializers
from src.infrastructure.api.rest.serializers.instruments import InstrumentRequestSerializer


class ContentFilterSerializer(serializers.Serializer):
    search = serializers.CharField(max_length=200, allow_blank=True, required=False)
    activo = serializers.BooleanField(required=False)
    page = serializers.IntegerField(min_value=1, default=1)


class QuestionSerializer(InstrumentRequestSerializer):
    texto = serializers.CharField()
    orden = serializers.IntegerField(min_value=1, max_value=32767)
    tipo_respuesta = serializers.ChoiceField(choices=['ESCALA', 'TEXTO', 'NUMERO', 'BOOLEANO'])
    escala_id = serializers.UUIDField(allow_null=True, required=False)
    obligatoria = serializers.BooleanField(required=False)
    invertida = serializers.BooleanField(required=False)


class ScaleSerializer(InstrumentRequestSerializer):
    nombre = serializers.CharField(max_length=150)
    descripcion = serializers.CharField(allow_blank=True, required=False)


class OptionSerializer(InstrumentRequestSerializer):
    etiqueta = serializers.CharField(max_length=150)
    valor = serializers.IntegerField(min_value=-32768, max_value=32767)
    orden = serializers.IntegerField(min_value=1, max_value=32767)


class RangeSerializer(InstrumentRequestSerializer):
    nombre = serializers.CharField(max_length=150)
    puntaje_minimo = serializers.IntegerField(min_value=-2147483648, max_value=2147483647)
    puntaje_maximo = serializers.IntegerField(min_value=-2147483648, max_value=2147483647)
    orden = serializers.IntegerField(min_value=1, max_value=32767)
    interpretacion = serializers.CharField(allow_blank=True, required=False)


class MoveContentSerializer(InstrumentRequestSerializer):
    direction = serializers.ChoiceField(choices=['up', 'down'])


CONTENT_SERIALIZERS = {'questions': QuestionSerializer, 'scales': ScaleSerializer,
                       'options': OptionSerializer, 'ranges': RangeSerializer}
