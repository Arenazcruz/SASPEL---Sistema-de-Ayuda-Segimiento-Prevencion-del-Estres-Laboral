from src.domain.exceptions.superadmin import AdministrationError


def exigir_version_editable(utilizada):
    if utilizada:
        raise AdministrationError('Esta versión ya tiene aplicaciones. Crea una nueva versión y escala para cambiar su contenido.')
