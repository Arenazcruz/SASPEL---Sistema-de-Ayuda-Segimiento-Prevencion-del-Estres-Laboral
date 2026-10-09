"""ORM del catálogo existente. La BD resuelve la unicidad incluso ante altas simultáneas."""

from dataclasses import asdict
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from src.application.dto.instruments import InstrumentDTO, InstrumentPage
from src.domain.exceptions.superadmin import AdministrationError, PersonNotFound
from src.infrastructure.persistence.django.models import InstrumentoPsicologico

PAGE_SIZE = 20


class DjangoInstrumentRepository:
    @staticmethod
    def dto(row):
        return InstrumentDTO(**{field: getattr(row, field) for field in InstrumentDTO.__dataclass_fields__})

    @staticmethod
    def find(instrument_id, lock=False):
        rows = InstrumentoPsicologico.objects.all()
        if lock:
            rows = rows.select_for_update()
        try:
            return rows.get(pk=instrument_id)
        except InstrumentoPsicologico.DoesNotExist:
            raise PersonNotFound('El instrumento no existe.') from None

    def list(self, filters):
        rows = InstrumentoPsicologico.objects.all()
        if filters.search:
            rows = rows.filter(Q(codigo__icontains=filters.search) | Q(nombre__icontains=filters.search)
                               | Q(version__icontains=filters.search))
        for field in ('activo', 'es_inicial'):
            value = getattr(filters, field)
            if value is not None:
                rows = rows.filter(**{field: value})
        count = rows.count()
        start = (filters.page - 1) * PAGE_SIZE
        rows = rows.order_by('codigo', 'version', 'pk')[start:start + PAGE_SIZE]
        return InstrumentPage(count, filters.page, PAGE_SIZE, [self.dto(row) for row in rows])

    def get(self, instrument_id):
        return self.dto(self.find(instrument_id))

    def save(self, row, fields=None):
        try:
            # El savepoint permite traducir una colisión sin dejar rota la transacción exterior.
            with transaction.atomic():
                row.full_clean(validate_constraints=False)
                row.save(update_fields=fields)
        except ValidationError as error:
            field, messages = next(iter(error.message_dict.items()))
            raise AdministrationError(' '.join(messages), field) from error
        except IntegrityError as error:
            if InstrumentoPsicologico.objects.filter(codigo=row.codigo, version=row.version).exclude(pk=row.pk).exists():
                raise AdministrationError('Ya existe un instrumento con este código y versión.', 'version') from error
            raise
        return self.dto(row)

    def create(self, data):
        return self.save(InstrumentoPsicologico(**asdict(data)))

    def update(self, instrument_id, changes):
        with transaction.atomic():
            row = self.find(instrument_id, lock=True)
            for field, value in changes.items():
                setattr(row, field, value)
            return self.save(row, [*changes, 'actualizado_en'])

    def set_active(self, instrument_id, active):
        with transaction.atomic():
            row = self.find(instrument_id, lock=True)
            row.activo = active
            row.save(update_fields=['activo', 'actualizado_en'])
            return self.dto(row)
