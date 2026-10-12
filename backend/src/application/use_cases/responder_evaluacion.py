from decimal import Decimal, InvalidOperation

from src.application.ports.output.responder_evaluacion import ResponderEvaluacionRepository
from src.domain.exceptions.evaluacion import EvaluacionError


class GestionarRespuestasEvaluacion:
    def __init__(self, repository: ResponderEvaluacionRepository):
        self.repository = repository

    def consultar(self, usuario_id, asignacion_id):
        with self.repository.atomic(usuario_id, asignacion_id):
            return self.repository.consultar(usuario_id, asignacion_id)

    def iniciar(self, usuario_id, asignacion_id):
        with self.repository.atomic(usuario_id, asignacion_id):
            detail = self.repository.consultar(usuario_id, asignacion_id)
            if detail.estado_asignacion == 'EN_PROGRESO' and detail.estado_aplicacion == 'INICIADA':
                return detail
            if detail.estado_asignacion != 'PENDIENTE' or detail.aplicacion_id is not None:
                raise EvaluacionError('Esta evaluación no se puede iniciar.')
            if not detail.disponible:
                raise EvaluacionError('La evaluación inicial todavía está siendo configurada.')
            self.repository.iniciar(usuario_id, asignacion_id)
            return self.repository.consultar(usuario_id, asignacion_id)

    @staticmethod
    def editable(detail):
        if detail.estado_asignacion != 'EN_PROGRESO' or detail.estado_aplicacion != 'INICIADA':
            raise EvaluacionError('Esta evaluación ya no admite cambios.')
        if not detail.disponible:
            raise EvaluacionError('La evaluación inicial todavía está siendo configurada.')

    @staticmethod
    def respondida(answer):
        return any(value is not None for value in (
            answer.opcion_id, answer.valor_texto, answer.valor_numerico, answer.valor_booleano,
        ))

    def validar(self, detail, respuestas):
        questions = {p.id: p for p in detail.preguntas}
        seen = set()
        for answer in respuestas:
            question = questions.get(answer.pregunta_id)
            if question is None or question.id in seen:
                raise EvaluacionError('La pregunta no está disponible en esta evaluación o está repetida.')
            seen.add(question.id)
            values = {
                'ESCALA': answer.opcion_id, 'TEXTO': answer.valor_texto,
                'NUMERO': answer.valor_numerico, 'BOOLEANO': answer.valor_booleano,
            }
            if any(value is not None for kind, value in values.items() if kind != question.tipo_respuesta):
                raise EvaluacionError(f'La respuesta de la pregunta {question.orden} no corresponde a su tipo.')
            value = values[question.tipo_respuesta]
            if value is None:
                continue  # Permite borrar una respuesta sin borrar su historial de auditoría.
            if question.tipo_respuesta == 'ESCALA' and value not in {o.id for o in question.opciones}:
                raise EvaluacionError(f'Selecciona una opción disponible para la pregunta {question.orden}.')
            if question.tipo_respuesta == 'TEXTO' and (not isinstance(value, str) or not value.strip()):
                raise EvaluacionError(f'Escribe una respuesta para la pregunta {question.orden}.')
            if question.tipo_respuesta == 'BOOLEANO' and type(value) is not bool:
                raise EvaluacionError('La respuesta debe ser Sí o No.')
            if question.tipo_respuesta == 'NUMERO':
                try:
                    number = Decimal(value)
                    if not number.is_finite() or abs(number) >= Decimal('100000000') or number != number.quantize(Decimal('0.0001')):
                        raise InvalidOperation
                except (InvalidOperation, ValueError, TypeError):
                    raise EvaluacionError('Introduce un número válido con hasta cuatro decimales.') from None

    def guardar(self, usuario_id, asignacion_id, respuestas):
        with self.repository.atomic(usuario_id, asignacion_id):
            detail = self.repository.consultar(usuario_id, asignacion_id)
            self.editable(detail)
            self.validar(detail, respuestas)
            self.repository.guardar(usuario_id, detail.aplicacion_id, respuestas)
            return self.repository.consultar(usuario_id, asignacion_id)

    def finalizar(self, usuario_id, asignacion_id, respuestas):
        with self.repository.atomic(usuario_id, asignacion_id):
            detail = self.repository.consultar(usuario_id, asignacion_id)
            self.editable(detail)
            self.validar(detail, respuestas)
            self.repository.guardar(usuario_id, detail.aplicacion_id, respuestas)
            detail = self.repository.consultar(usuario_id, asignacion_id)
            self.validar(detail, detail.respuestas)
            answered = {r.pregunta_id for r in detail.respuestas if self.respondida(r)}
            missing = tuple(p.id for p in detail.preguntas if p.obligatoria and p.id not in answered)
            if missing:
                raise EvaluacionError('Responde las preguntas obligatorias antes de finalizar.', missing)
            self.repository.finalizar(usuario_id, asignacion_id, detail.aplicacion_id)
            return self.repository.consultar(usuario_id, asignacion_id)
