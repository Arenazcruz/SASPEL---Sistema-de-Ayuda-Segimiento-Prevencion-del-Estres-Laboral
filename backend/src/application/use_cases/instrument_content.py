from dataclasses import asdict
from typing import Literal
from uuid import UUID

from src.application.dto.instrument_content import (
    ContentData, ContentFilters, ContentKind, QuestionData, ScaleData, OptionData, RangeData,
)
from src.application.ports.input.instrument_content import ContentAdministration
from src.application.ports.output.instrument_content import ContentRepository
from src.domain.exceptions.superadmin import AdministrationError
from src.domain.services.instrument_content import validate_content

DATA_TYPES = {'questions': QuestionData, 'scales': ScaleData, 'options': OptionData, 'ranges': RangeData}


class ManageInstrumentContent(ContentAdministration):
    def __init__(self, repository: ContentRepository):
        self.repository = repository

    def list(self, kind: ContentKind, parent_id: UUID | None, filters: ContentFilters):
        return self.repository.list(kind, parent_id, filters)

    def get(self, kind: ContentKind, parent_id: UUID | None, item_id: UUID):
        return self.repository.get(kind, parent_id, item_id)

    def validate(self, kind, values, previous=None):
        values = validate_content(kind, values)
        if kind == 'questions' and values['escala_id']:
            scale = self.repository.get('scales', None, values['escala_id'], lock=True)
            if not scale.activo and (previous is None or previous.escala_id != scale.id):
                raise AdministrationError('Selecciona una escala activa.', 'escala_id')
        return values

    def create(self, kind: ContentKind, parent_id: UUID | None, data: ContentData):
        if not isinstance(data, DATA_TYPES[kind]):
            raise AdministrationError('Los campos no corresponden al catálogo.')
        with self.repository.atomic(kind, parent_id):
            return self.repository.create(kind, parent_id, self.validate(kind, asdict(data)))

    def edit(self, kind: ContentKind, parent_id: UUID | None, item_id: UUID, changes: dict):
        fields = DATA_TYPES[kind].__dataclass_fields__
        if set(changes) - fields.keys():
            raise AdministrationError('Solo se admiten los campos editables del catálogo.')
        with self.repository.atomic(kind, parent_id):
            previous = self.repository.get(kind, parent_id, item_id, lock=True)
            values = {name: getattr(previous, name) for name in fields} | changes
            return self.repository.update(kind, parent_id, item_id, self.validate(kind, values, previous))

    def set_active(self, kind: ContentKind, parent_id: UUID | None, item_id: UUID, active: bool):
        with self.repository.atomic(kind, parent_id):
            return self.repository.update(kind, parent_id, item_id, {'activo': active})

    def move(self, kind: ContentKind, parent_id: UUID, item_id: UUID, direction: Literal['up', 'down']):
        if kind not in ('questions', 'options') or direction not in ('up', 'down'):
            raise AdministrationError('Movimiento no válido.')
        with self.repository.atomic(kind, parent_id):
            return self.repository.move(kind, parent_id, item_id, direction)
