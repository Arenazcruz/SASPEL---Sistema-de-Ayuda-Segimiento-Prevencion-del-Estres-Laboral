import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from src.infrastructure.persistence.django.models import (
    EscalaRespuesta, InstrumentoPsicologico, OpcionRespuesta, RangoInterpretacion,
)


CONFIG_PATH = Path(__file__).resolve().parent.parent / 'data' / 'initial_instrument.json'


class Command(BaseCommand):
    help = 'Prepara instrumento inicial, escala y rangos desde configuración, sin crear preguntas ni asignaciones.'

    @staticmethod
    def ensure(model, lookup, data):
        row, created = model.objects.select_for_update().get_or_create(**lookup, defaults=data)
        if not created:
            # No sobrescribir contenido aprobado, opciones o rangos usados históricamente.
            changed = [field for field, value in data.items() if getattr(row, field) != value]
            if any(field not in ('activo', 'es_inicial', 'deleted') for field in changed):
                raise CommandError(f'{model.__name__}: la configuración existente difiere; revisa la versión antes de cargarla.')
            if changed:
                for field in changed:
                    setattr(row, field, data[field])
                row.full_clean()
                row.actualizado_por = 'SYSTEM'
                row.save(update_fields=[*changed, 'actualizado_por'])
        return row

    def handle(self, *args, **options):
        config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        instrument_data = dict(config['instrumento'])
        key = {field: instrument_data.pop(field) for field in ('codigo', 'version')}
        try:
            with transaction.atomic():
                other = InstrumentoPsicologico.objects.filter(activo=True, es_inicial=True).exclude(**key)
                if other.exists():
                    raise CommandError('Ya existe otro instrumento inicial activo. No se modificó su configuración.')
                instrument = self.ensure(InstrumentoPsicologico, key, instrument_data | {'deleted': False})
                scale_data = dict(config['escala'])
                scale = self.ensure(EscalaRespuesta, {'nombre': scale_data.pop('nombre')}, scale_data | {'deleted': False})
                if scale.opciones.exclude(valor__in=[option['valor'] for option in config['opciones']]).exists():
                    raise CommandError('La escala existente contiene valores adicionales. No se modificaron sus opciones.')
                for option in config['opciones']:
                    self.ensure(OpcionRespuesta, {'escala': scale, 'valor': option['valor']},
                                option | {'activo': True, 'deleted': False})
                if instrument.rangos.exclude(nombre__in=[item['nombre'] for item in config['rangos']]).exists():
                    raise CommandError('El instrumento tiene rangos adicionales. No se modificaron sus rangos.')
                for item in config['rangos']:
                    self.ensure(RangoInterpretacion, {'instrumento': instrument, 'nombre': item['nombre']},
                                item | {'activo': True, 'deleted': False})
        except (ValidationError, IntegrityError) as error:
            raise CommandError('La configuración entra en conflicto con datos existentes; se revirtió la carga.') from error
        questions = config['configuracion_preguntas']
        self.stdout.write(self.style.SUCCESS(
            f"{key['codigo']} {key['version']}: instrumento, escala, {len(config['opciones'])} opciones y "
            f"{len(config['rangos'])} rangos preparados. Sin preguntas nuevas."
        ))
        self.stdout.write(
            f"Carga posterior en Superadmin: {questions['cantidad']} ítems {questions['tipo_respuesta']}, "
            f"obligatoria={questions['obligatoria']}, orden desde {questions['orden_inicial']}; "
            f"invertidos: {', '.join(map(str, questions['ordenes_invertidos']))}."
        )
