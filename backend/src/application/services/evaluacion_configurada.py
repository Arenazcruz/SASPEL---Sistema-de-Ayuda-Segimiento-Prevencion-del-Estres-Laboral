from src.application.dto.responder_evaluacion import PreguntaEvaluacion


def contenido_disponible(preguntas: tuple[PreguntaEvaluacion, ...]) -> bool:
    return bool(preguntas) and all(
        p.tipo_respuesta in ('ESCALA', 'TEXTO', 'NUMERO', 'BOOLEANO')
        and (p.tipo_respuesta != 'ESCALA' or bool(p.opciones)) for p in preguntas
    )
