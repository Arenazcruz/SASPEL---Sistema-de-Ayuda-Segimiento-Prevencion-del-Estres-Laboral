from src.domain.exceptions.superadmin import AdministrationError


def validar_transicion_alerta(actual, nuevo):
    permitidos = {'ABIERTA': {'EN_ATENCION','CERRADA'}, 'EN_ATENCION': {'EN_ATENCION','CERRADA'}, 'CERRADA': set()}
    if nuevo not in permitidos.get(actual,set()):
        raise AdministrationError('La alerta cerrada no admite cambios y la transición debe ser válida.')
