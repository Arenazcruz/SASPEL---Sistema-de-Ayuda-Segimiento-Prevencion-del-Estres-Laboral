from src.application.ports.input.responder_evaluacion import ResponderEvaluacion
from src.application.use_cases.responder_evaluacion import GestionarRespuestasEvaluacion
from src.infrastructure.persistence.django.repositories.responder_evaluacion import DjangoResponderEvaluacionRepository
from src.infrastructure.persistence.django.repositories.assignments import DjangoAssignmentRepository


def build_responder_evaluacion() -> ResponderEvaluacion:
    return GestionarRespuestasEvaluacion(DjangoResponderEvaluacionRepository(), DjangoAssignmentRepository())
