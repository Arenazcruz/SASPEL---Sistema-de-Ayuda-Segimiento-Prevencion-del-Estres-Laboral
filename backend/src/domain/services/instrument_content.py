"""Reglas del catálogo; no aplica cuestionarios ni calcula resultados."""

from src.domain.exceptions.superadmin import AdministrationError


def validate_content(kind: str, data: dict) -> dict:
    data = dict(data)
    if kind == 'questions':
        if data['tipo_respuesta'] not in ('ESCALA', 'TEXTO', 'NUMERO', 'BOOLEANO'):
            raise AdministrationError('Selecciona un tipo de respuesta válido.', 'tipo_respuesta')
        if data['tipo_respuesta'] == 'ESCALA' and data['escala_id'] is None:
            raise AdministrationError('Selecciona una escala de respuesta.', 'escala_id')
        if data['tipo_respuesta'] != 'ESCALA' and data['escala_id'] is not None:
            raise AdministrationError('Solo las preguntas de tipo ESCALA admiten escala.', 'escala_id')
    if kind == 'ranges' and data['puntaje_minimo'] > data['puntaje_maximo']:
        raise AdministrationError('El mínimo no puede superar al máximo.', 'puntaje_minimo')
    return data
