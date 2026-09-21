"""Validaciones de datos personales, sin dependencias de Django ni HTTP."""

from datetime import date
import re
import unicodedata

from src.domain.exceptions.superadmin import AdministrationError


def validate_name(value: str, field: str) -> str:
    value = re.sub(' +', ' ', unicodedata.normalize('NFC', value).strip())
    if not value and field in {'apellido_materno', 'nombre_preferido'}:
        return ''
    for word in value.split(' '):
        if not word or not word[0].isalpha() or any(
            not char.isalpha() and not unicodedata.category(char).startswith('M') for char in word
        ):
            raise AdministrationError('Usa solo letras y espacios; se permiten tildes y ñ.', field)
    return value


def validate_employee_code(value: str) -> str:
    value = value.strip()
    if not re.fullmatch(r'[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*', value):
        raise AdministrationError('Usa letras y números, con guiones entre grupos; sin espacios.', 'codigo_empleado')
    return value


def validate_phone(value: str) -> str:
    value = value.strip()
    if value and not re.fullmatch(r'[0-9]{8,15}', value):
        raise AdministrationError('El teléfono debe contener entre 8 y 15 dígitos, sin letras ni símbolos.', 'telefono')
    return value


def validate_birth_date(value: date, today: date) -> date:
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if not 18 < age < 78:
        raise AdministrationError('La edad debe ser mayor de 18 y menor de 78 años (19 a 77 años cumplidos).', 'fecha_nacimiento')
    return value
