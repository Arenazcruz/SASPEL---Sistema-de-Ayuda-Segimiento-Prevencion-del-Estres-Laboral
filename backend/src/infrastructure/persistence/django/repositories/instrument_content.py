"""Persistencia T25 sobre tablas existentes, con bloqueo por instrumento/escala."""

from contextlib import contextmanager
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q

from src.application.dto.instrument_content import (
    ContentKind, ContentPage, QuestionDTO, ScaleDTO, OptionDTO, RangeDTO,
)
from src.domain.exceptions.superadmin import AdministrationError, PersonNotFound
from src.infrastructure.persistence.django.models import (
    InstrumentoPsicologico, PreguntaInstrumento, EscalaRespuesta, OpcionRespuesta, RangoInterpretacion,
)

CATALOGS = {
    'questions': (PreguntaInstrumento, QuestionDTO, 'instrumento_id', InstrumentoPsicologico, ('texto',)),
    'scales': (EscalaRespuesta, ScaleDTO, None, None, ('nombre', 'descripcion')),
    'options': (OpcionRespuesta, OptionDTO, 'escala_id', EscalaRespuesta, ('etiqueta',)),
    'ranges': (RangoInterpretacion, RangeDTO, 'instrumento_id', InstrumentoPsicologico, ('nombre', 'interpretacion')),
}
PAGE_SIZE = 20


class DjangoContentRepository:
    @staticmethod
    def parent(kind, parent_id, lock=False):
        model = CATALOGS[kind][3]
        if model is not None:
            rows = model.objects.select_for_update() if lock else model.objects.all()
            if not rows.filter(pk=parent_id).first():
                raise PersonNotFound('El instrumento o la escala no existe.')

    @contextmanager
    def atomic(self, kind: ContentKind, parent_id: UUID | None):
        try:
            with transaction.atomic():
                self.parent(kind, parent_id, lock=True)
                yield
        except ValidationError as error:
            if hasattr(error, 'message_dict'):
                field, messages = next(iter(error.message_dict.items()))
            else:
                field, messages = 'detail', error.messages
            raise AdministrationError(' '.join(messages), field) from error
        except IntegrityError as error:
            raise AdministrationError('Ya existe un registro con ese nombre, orden o valor. Revisa los datos.') from error

    @staticmethod
    def rows(kind, parent_id):
        model, _, field, _, _ = CATALOGS[kind]
        rows = model.objects.all()
        return rows.filter(**{field: parent_id}) if field else rows

    @staticmethod
    def dto(kind, row):
        dto = CATALOGS[kind][1]
        return dto(**{field: getattr(row, field) for field in dto.__dataclass_fields__})

    def find(self, kind, parent_id, item_id, lock=False):
        rows = self.rows(kind, parent_id)
        if lock:
            rows = rows.select_for_update()
        row = rows.filter(pk=item_id).first()
        if row is None:
            raise PersonNotFound('El registro no existe en este instrumento o escala.')
        return row

    def list(self, kind: ContentKind, parent_id: UUID | None, filters):
        self.parent(kind, parent_id)
        rows = self.rows(kind, parent_id)
        if filters.search:
            query = Q()
            for name in CATALOGS[kind][4]:
                query |= Q(**{name + '__icontains': filters.search})
            rows = rows.filter(query)
        if filters.activo is not None:
            rows = rows.filter(activo=filters.activo)
        count = rows.count()
        start = (filters.page - 1) * PAGE_SIZE
        rows = rows.order_by('nombre' if kind == 'scales' else 'orden', 'pk')[start:start + PAGE_SIZE]
        return ContentPage(count, filters.page, PAGE_SIZE, [self.dto(kind, row) for row in rows])

    def get(self, kind: ContentKind, parent_id: UUID | None, item_id: UUID, *, lock=False):
        return self.dto(kind, self.find(kind, parent_id, item_id, lock=lock))

    def create(self, kind: ContentKind, parent_id: UUID | None, data: dict):
        model, _, parent_field, _, _ = CATALOGS[kind]
        row = model(**data, **({parent_field: parent_id} if parent_field else {}))
        row.full_clean()
        row.save()
        return self.dto(kind, row)

    def update(self, kind: ContentKind, parent_id: UUID | None, item_id: UUID, data: dict):
        row = self.find(kind, parent_id, item_id, lock=True)
        for name, value in data.items():
            setattr(row, name, value)
        row.full_clean()
        row.save(update_fields=[*data, 'actualizado_en'])
        return self.dto(kind, row)

    def move(self, kind: ContentKind, parent_id: UUID, item_id: UUID, direction):
        row = self.find(kind, parent_id, item_id, lock=True)
        rows = self.rows(kind, parent_id)
        neighbor = (rows.filter(orden__lt=row.orden).order_by('-orden') if direction == 'up'
                    else rows.filter(orden__gt=row.orden).order_by('orden')).select_for_update().first()
        if neighbor is None:
            return self.dto(kind, row)
        # Intercambio en dos pasos: respeta la unicidad inmediata de PostgreSQL.
        used = set(rows.values_list('orden', flat=True))
        free = next((n for n in range(32768) if n not in used), None)
        if free is None:
            raise AdministrationError('No hay un orden libre para completar el movimiento.', 'orden')
        old_order = row.orden
        row.orden = free
        row.save(update_fields=['orden'])
        row.orden = neighbor.orden
        neighbor.orden = old_order
        neighbor.save(update_fields=['orden'])
        row.save(update_fields=['orden'])
        return self.dto(kind, row)
