"""Define campos HTTP aceptados por administración. Los serializers estrictos rechazan campos
extra; los filtros usan el serializer estándar. Cambiar campos requiere revisar DTO, casos y
formularios Angular, sin trasladar aquí reglas inexistentes.
"""

from rest_framework import serializers
from src.domain.value_objects.functional_role import FunctionalRole


class StrictSerializer(serializers.Serializer):
    """Base de solicitudes de escritura: impide enviar campos a operaciones que no los ofrecen."""
    def to_internal_value(self, data):
        """Exige objeto JSON y rechaza claves desconocidas con errores por campo; luego devuelve
        la validación normal de DRF.
        """
        if not isinstance(data, dict):
            raise serializers.ValidationError('Se requiere un objeto JSON.')
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: 'Campo no permitido en esta operación.' for key in unknown})
        return super().to_internal_value(data)


class UserEditSerializer(StrictSerializer):
    """Datos personales editables: correo, nombres, código, contacto, fecha/sexo,
    area_id/cargo_id y habilitación. PATCH usa partial=True; no acepta rol, estado ni claves.
    """
    email = serializers.EmailField(max_length=150)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    apellido_materno = serializers.CharField(max_length=150, allow_blank=True)
    codigo_empleado = serializers.CharField(max_length=50)
    nombre_preferido = serializers.CharField(max_length=150, allow_blank=True, required=False)
    fecha_nacimiento = serializers.DateField(allow_null=True, required=False)
    sexo = serializers.ChoiceField(choices=['', 'F', 'M', 'O'], required=False)
    telefono = serializers.CharField(max_length=30, allow_blank=True, required=False)
    area_id = serializers.IntegerField(min_value=1, allow_null=True, required=False)
    cargo_id = serializers.IntegerField(min_value=1, allow_null=True, required=False)
    habilitado_asignaciones = serializers.BooleanField(required=False)


class UserCreateSerializer(UserEditSerializer):
    """Añade rol, clave y confirmación a los datos personales del alta. El serializer reconoce
    TRABAJADOR, pero CreateUser prohíbe crearlo directamente.
    """
    role = serializers.ChoiceField(choices=[role.value for role in FunctionalRole])
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)
    password_confirmation = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)

    def validate(self, data):
        """Comprueba coincidencia de claves y elimina password_confirmation del diccionario que
        formará CreateUserCommand. No guarda ni aplica aquí la fortaleza de contraseña.
        """
        if data['password'] != data.pop('password_confirmation'):
            raise serializers.ValidationError({'password_confirmation': 'Las contraseñas no coinciden.'})
        return data


class UserFilterSerializer(serializers.Serializer):
    """Valida search, role, active, area, cargo y page en query params. Page comienza en 1; los
    demás filtros ausentes no restringen resultados.
    """
    search = serializers.CharField(required=False, allow_blank=True, max_length=200)
    role = serializers.ChoiceField(choices=[role.value for role in FunctionalRole], required=False)
    active = serializers.BooleanField(required=False)
    area = serializers.IntegerField(min_value=1, required=False)
    cargo = serializers.IntegerField(min_value=1, required=False)
    page = serializers.IntegerField(min_value=1, required=False, default=1)


class PasswordSerializer(StrictSerializer):
    """Acepta únicamente password/password_confirmation para reset-password; coincidencia y
    fortaleza las comprueba el caso.
    """
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)
    password_confirmation = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)


class RoleSerializer(StrictSerializer):
    """Acepta únicamente role para la acción dedicada; ChangeUserRole comprueba si la transición
    está permitida.
    """
    role = serializers.ChoiceField(choices=[role.value for role in FunctionalRole])


class InstitutionSerializer(StrictSerializer):
    """Acepta nombre y descripcion para áreas/cargos. La activación usa otra acción; duplicados
    se comprueban en el repositorio.
    """
    nombre = serializers.CharField(max_length=150)
    descripcion = serializers.CharField(required=False, allow_blank=True, max_length=5000)
