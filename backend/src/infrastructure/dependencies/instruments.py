from src.infrastructure.persistence.django.repositories.instruments import DjangoInstrumentRepository


def build_instruments(case):
    return case(DjangoInstrumentRepository())
