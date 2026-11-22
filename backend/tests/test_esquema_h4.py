from django.apps import apps
from django.db import connection, models
from django.test import TestCase


class EsquemaPostgresTests(TestCase):
    def test_catalogo_fisico_corresponde_a_la_definicion_de_cada_modelo(self):
        with connection.cursor() as cursor:
            for model in apps.get_app_config('api').get_models():
                meta = model._meta
                with self.subTest(tabla=meta.db_table):
                    constraints = connection.introspection.get_constraints(cursor, meta.db_table)
                    columns = {c.name: c for c in connection.introspection.get_table_description(cursor, meta.db_table)}
                    for declaration in [*meta.constraints, *meta.indexes]:
                        self.assertIn(declaration.name, constraints)
                    for field in meta.local_fields:
                        self.assertIn(field.column, columns)
                        self.assertEqual(columns[field.column].null_ok, field.null)
                        if isinstance(field, models.ForeignKey):
                            target = (field.target_field.model._meta.db_table, field.target_field.column)
                            self.assertTrue(any(c['foreign_key'] == target and c['columns'] == [field.column]
                                                for c in constraints.values()), field.name)
                        if field.unique:
                            self.assertTrue(any((c['primary_key'] or c['unique']) and c['columns']==[field.column]
                                                for c in constraints.values()), field.name)
