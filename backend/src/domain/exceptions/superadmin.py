"""Errores administrativos que SuperadminView traduce a respuestas HTTP."""


class AdministrationError(Exception):
    """Rechazo con message y field (detail por defecto); la vista responde 400 por campo."""
    def __init__(self, message: str, field: str = 'detail'):
        super().__init__(message)
        self.field = field


class PersonNotFound(AdministrationError):
    """Persona o catálogo ausente; la vista responde 404."""
    pass
