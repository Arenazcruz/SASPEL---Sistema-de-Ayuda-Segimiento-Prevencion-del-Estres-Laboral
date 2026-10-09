from src.application.use_cases.instrument_content import ManageInstrumentContent
from src.infrastructure.persistence.django.repositories.instrument_content import DjangoContentRepository


def build_content():
    return ManageInstrumentContent(DjangoContentRepository())
