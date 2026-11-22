from src.application.ports.input.resultados import ConsultaResultados
from src.application.use_cases.resultados import ConsultarResultados
from src.infrastructure.persistence.django.repositories.resultados import DjangoResultadosRepository


def build_resultados() -> ConsultaResultados:
    return ConsultarResultados(DjangoResultadosRepository())
