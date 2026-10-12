from io import StringIO
from uuid import UUID

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from src.infrastructure.persistence.django.management.commands.seed_institution_catalogs import AREAS, CARGOS
from src.infrastructure.persistence.django.models import AreaInstitucional, CargoInstitucional


class SeedInstitutionCatalogsTests(TestCase):
    def test_catalogs_preserve_identity_other_records_and_are_idempotent(self):
        user = get_user_model().objects.create_superuser(
            username='catalogs@saspel.com', email='catalogs@saspel.com', password=None,
        )
        user.groups.add(Group.objects.get(name='SUPERADMIN'))
        user_before = get_user_model().objects.values().get(pk=user.pk)
        groups_before = list(user.groups.values_list('pk', flat=True))
        original = {}
        untouched = {}
        for model, names, expected in ((AreaInstitucional, AREAS, 9), (CargoInstitucional, CARGOS, 111)):
            self.assertEqual(len(names), expected)
            self.assertEqual(len(set(names)), expected)
            row = model.objects.create(nombre=names[0], descripcion='Conservar descripción',
                                       activo=False, deleted=True, creado_por='IMPORT')
            original[model] = row
            extra = model.objects.create(nombre='Registro ajeno a la lista', activo=False, deleted=True)
            untouched[model] = model.objects.values().get(pk=extra.pk)

        call_command('seed_institution_catalogs', stdout=StringIO())
        first_run = {}
        for model, names in ((AreaInstitucional, AREAS), (CargoInstitucional, CARGOS)):
            self.assertEqual(model.objects.filter(nombre__in=names).count(), len(names))
            self.assertEqual(model.objects.count(), len(names) + 1)
            for row in model.objects.filter(nombre__in=names):
                self.assertIsInstance(row.pk, UUID)
                self.assertTrue(row.activo)
                self.assertFalse(row.deleted)
                self.assertIsNotNone(row.creado_en)
                self.assertIsNotNone(row.actualizado_en)
                self.assertTrue(row.creado_por)
                self.assertTrue(row.actualizado_por)
            previous = original[model]
            current = model.objects.get(nombre=names[0])
            self.assertEqual(current.pk, previous.pk)
            self.assertEqual(current.creado_en, previous.creado_en)
            self.assertEqual(current.creado_por, 'IMPORT')
            self.assertEqual(current.descripcion, 'Conservar descripción')
            extra_before = untouched[model]
            self.assertEqual(model.objects.values().get(pk=extra_before['id']), extra_before)
            first_run[model] = list(model.objects.order_by('pk').values())

        output = StringIO()
        call_command('seed_institution_catalogs', stdout=output)
        self.assertEqual(output.getvalue().count('0 creados, 0 reactivados'), 2)
        for model, rows in first_run.items():
            self.assertEqual(list(model.objects.order_by('pk').values()), rows)
        self.assertEqual(get_user_model().objects.values().get(pk=user.pk), user_before)
        self.assertEqual(list(user.groups.values_list('pk', flat=True)), groups_before)
