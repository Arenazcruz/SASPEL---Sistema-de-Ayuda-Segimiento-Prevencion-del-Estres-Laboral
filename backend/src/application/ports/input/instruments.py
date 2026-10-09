"""Entradas de T25-A: catálogo, ficha, alta, edición y estado."""

from typing import Protocol
from src.application.dto.instruments import InstrumentDTO, InstrumentData, InstrumentFilters, InstrumentPage


class InstrumentListing(Protocol):
    def execute(self, filters: InstrumentFilters) -> InstrumentPage: ...


class InstrumentDetail(Protocol):
    def execute(self, instrument_id: int) -> InstrumentDTO: ...


class InstrumentCreation(Protocol):
    def execute(self, data: InstrumentData) -> InstrumentDTO: ...


class InstrumentEditing(Protocol):
    def execute(self, instrument_id: int, changes: dict) -> InstrumentDTO: ...


class InstrumentActivation(Protocol):
    def execute(self, instrument_id: int, active: bool) -> InstrumentDTO: ...
