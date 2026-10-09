"""Administra metadatos y estado, sin intervenir en el contenido ni aplicación de pruebas."""

from uuid import UUID

from src.application.dto.instruments import InstrumentDTO, InstrumentData, InstrumentFilters, InstrumentPage
from src.application.ports.input.instruments import (
    InstrumentActivation, InstrumentCreation, InstrumentDetail, InstrumentEditing, InstrumentListing,
)
from src.application.ports.output.instruments import InstrumentRepository
from src.domain.exceptions.superadmin import AdministrationError

EDITABLE_FIELDS = {'codigo', 'nombre', 'version', 'descripcion', 'instrucciones', 'es_inicial'}


class InstrumentCase:
    def __init__(self, repository: InstrumentRepository):
        self.repository = repository


class ListInstruments(InstrumentCase, InstrumentListing):
    def execute(self, filters: InstrumentFilters) -> InstrumentPage:
        return self.repository.list(filters)


class GetInstrument(InstrumentCase, InstrumentDetail):
    def execute(self, instrument_id: UUID) -> InstrumentDTO:
        return self.repository.get(instrument_id)


class CreateInstrument(InstrumentCase, InstrumentCreation):
    def execute(self, data: InstrumentData) -> InstrumentDTO:
        return self.repository.create(data)


class EditInstrument(InstrumentCase, InstrumentEditing):
    def execute(self, instrument_id: UUID, changes: dict) -> InstrumentDTO:
        if set(changes) - EDITABLE_FIELDS:
            raise AdministrationError('La edición solo admite los metadatos del instrumento.')
        return self.repository.update(instrument_id, changes)


class SetInstrumentActive(InstrumentCase, InstrumentActivation):
    def execute(self, instrument_id: UUID, active: bool) -> InstrumentDTO:
        return self.repository.set_active(instrument_id, active)
