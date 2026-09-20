"""Reglas de correo institucional, independientes de HTTP y persistencia."""

import re
import unicodedata

from src.domain.exceptions.superadmin import AdministrationError


def institutional_email(first_name: str, last_name: str, sequence: int = 1) -> str:
    parts = []
    for value, field in ((first_name, 'first_name'), (last_name, 'last_name')):
        words = value.strip().split()
        normalized = unicodedata.normalize('NFKD', words[0] if words else '')
        part = re.sub(r'[^a-z0-9]', '', normalized.encode('ascii', 'ignore').decode().lower())
        if not part:
            raise AdministrationError('Indica un nombre o apellido con letras o números válidos.', field)
        parts.append(part)
    suffix = str(sequence) if sequence > 1 else ''
    # Mantiene el local-part dentro de 64 caracteres, incluido el sufijo de colisión.
    available = 63 - len(suffix)
    name_size = min(len(parts[0]), available // 2)
    surname_size = min(len(parts[1]), available - name_size)
    name_size = min(len(parts[0]), available - surname_size)
    return f'{parts[0][:name_size]}.{parts[1][:surname_size]}{suffix}@saspel.com'
