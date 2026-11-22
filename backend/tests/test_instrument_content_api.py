"""T25: operaciones HTTP reales y constraints en PostgreSQL temporal."""

from uuid import UUID, uuid4
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from src.infrastructure.persistence.django.models import (
    InstrumentoPsicologico, PreguntaInstrumento, EscalaRespuesta, OpcionRespuesta,
    RangoInterpretacion, AsignacionInstrumento, AplicacionInstrumento, RespuestaPregunta,
)

BASE = '/api/superadmin/'


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class InstrumentContentApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = get_user_model().objects.create_user(username='t25@saspel.com')
        cls.root.groups.add(Group.objects.get(name='SUPERADMIN'))
        cls.instrument = InstrumentoPsicologico.objects.create(codigo='T25', nombre='Prueba')
        cls.other = InstrumentoPsicologico.objects.create(codigo='T25', nombre='Otra versión', version='2')
        cls.scale = EscalaRespuesta.objects.create(nombre='Frecuencia', descripcion='Escala de prueba')
        cls.other_scale = EscalaRespuesta.objects.create(nombre='Otra escala')
        cls.question = PreguntaInstrumento.objects.create(
            instrumento=cls.instrument, texto='Primera pregunta', orden=1,
            tipo_respuesta='ESCALA', escala=cls.scale,
        )
        cls.option = OpcionRespuesta.objects.create(escala=cls.scale, etiqueta='Nunca', valor=0, orden=1)
        cls.interval = RangoInterpretacion.objects.create(
            instrumento=cls.instrument, nombre='Inicial', puntaje_minimo=0, puntaje_maximo=5, orden=1,
        )

    def setUp(self):
        self.client = APIClient()
        self.authorize(self.root)

    def authorize(self, user):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(user)))

    def path(self, kind, parent=None):
        if kind == 'scales':
            return BASE + 'scales/'
        if kind == 'options':
            return BASE + f'scales/{parent or self.scale.pk}/options/'
        return BASE + f'instruments/{parent or self.instrument.pk}/{kind}/'

    def create(self, kind, **changes):
        data = {
            'questions': {'texto': 'Nueva pregunta', 'orden': 2, 'tipo_respuesta': 'TEXTO'},
            'scales': {'nombre': 'Nueva escala'},
            'options': {'etiqueta': 'A veces', 'valor': 1, 'orden': 2},
            'ranges': {'nombre': 'Siguiente', 'puntaje_minimo': 6, 'puntaje_maximo': 10, 'orden': 2},
        }[kind] | changes
        return self.client.post(self.path(kind), data, format='json')

    def detail(self, kind, pk):
        return self.path(kind) + str(pk) + '/'

    def test_create_all_catalogs_with_uuid_defaults_and_audit(self):
        for kind, model in (('questions', PreguntaInstrumento), ('scales', EscalaRespuesta),
                            ('options', OpcionRespuesta), ('ranges', RangoInterpretacion)):
            with self.subTest(kind=kind):
                response = self.create(kind)
                self.assertEqual(response.status_code, 201, response.data)
                body = response.json()
                row = model.objects.get(pk=UUID(body['id']))
                self.assertTrue(row.activo)
                self.assertFalse(row.deleted)
                self.assertEqual(row.creado_por, 'SYSTEM')
                self.assertTrue(body['creado_en'])
                self.assertTrue(body['actualizado_en'])
                self.assertEqual(response['Cache-Control'], 'no-store')
                if kind in ('questions', 'ranges'):
                    self.assertEqual(body['instrumento_id'], str(self.instrument.pk))
                if kind == 'options':
                    self.assertEqual(body['escala_id'], str(self.scale.pk))
                    self.assertNotIn('pregunta_id', body)

    def test_question_properties_and_scale_relation(self):
        response = self.create('questions', tipo_respuesta='ESCALA', escala_id=str(self.scale.pk),
                               obligatoria=False, invertida=True)
        self.assertEqual(response.status_code, 201, response.data)
        row = PreguntaInstrumento.objects.get(pk=response.json()['id'])
        self.assertEqual(row.escala_id, self.scale.pk)
        self.assertFalse(row.obligatoria)
        self.assertTrue(row.invertida)
        self.assertEqual(self.client.get(self.detail('questions', row.pk)).json()['escala_id'], str(self.scale.pk))

    def test_question_requires_scale_only_for_scale_type(self):
        for values in ({'tipo_respuesta': 'ESCALA'}, {'tipo_respuesta': 'ESCALA', 'escala_id': None},
                       {'tipo_respuesta': 'TEXTO', 'escala_id': str(self.scale.pk)},
                       {'tipo_respuesta': 'INVALIDO'}, {'escala_id': 'not-a-uuid'}):
            with self.subTest(values=values):
                self.assertEqual(self.create('questions', **values).status_code, 400)
        self.assertEqual(self.create('questions', tipo_respuesta='ESCALA', escala_id=str(uuid4())).status_code, 404)
        for kind in ('TEXTO', 'NUMERO', 'BOOLEANO'):
            response = self.create('questions', tipo_respuesta=kind, orden={'TEXTO': 2, 'NUMERO': 3, 'BOOLEANO': 4}[kind])
            self.assertEqual(response.status_code, 201)
            self.assertIsNone(response.json()['escala_id'])

    def test_question_edit_validates_merged_values_and_explicitly_clears_scale(self):
        path = self.detail('questions', self.question.pk)
        self.assertEqual(self.client.patch(path, {'tipo_respuesta': 'NUMERO'}, format='json').status_code, 400)
        self.question.refresh_from_db()
        self.assertEqual(self.question.tipo_respuesta, 'ESCALA')
        response = self.client.patch(path, {'tipo_respuesta': 'NUMERO', 'escala_id': None}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()['escala_id'])
        self.assertEqual(self.client.patch(path, {'tipo_respuesta': 'ESCALA'}, format='json').status_code, 400)

    def test_inactive_scale_cannot_be_newly_associated_but_existing_link_survives(self):
        self.scale.activo = False
        self.scale.save()
        self.assertEqual(self.create('questions', tipo_respuesta='ESCALA', escala_id=str(self.scale.pk)).status_code, 400)
        response = self.client.patch(self.detail('questions', self.question.pk), {'texto': 'Editada'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['escala_id'], str(self.scale.pk))

    def test_search_status_pagination_and_order_are_scoped(self):
        PreguntaInstrumento.objects.create(instrumento=self.other, texto='Ajena', tipo_respuesta='TEXTO', orden=1)
        PreguntaInstrumento.objects.bulk_create([
            PreguntaInstrumento(instrumento=self.instrument, texto=f'Pregunta {index}', tipo_respuesta='TEXTO', orden=index)
            for index in range(2, 24)
        ])
        first = self.client.get(self.path('questions')).json()
        second = self.client.get(self.path('questions'), {'page': 2}).json()
        self.assertEqual((first['count'], len(first['results']), len(second['results'])), (23, 20, 3))
        self.assertEqual([r['orden'] for r in first['results']], list(range(1, 21)))
        self.assertFalse({r['id'] for r in first['results']} & {r['id'] for r in second['results']})
        self.question.activo = False
        self.question.save()
        filtered = self.client.get(self.path('questions'), {'search': 'Primera', 'activo': 'false'}).json()
        self.assertEqual([r['id'] for r in filtered['results']], [str(self.question.pk)])
        scales = self.client.get(self.path('scales'), {'search': 'frecuencia', 'activo': 'true'}).json()
        self.assertEqual([r['id'] for r in scales['results']], [str(self.scale.pk)])
        for query in ({'page': 0}, {'page': 'abc'}, {'activo': 'quizas'}, {'search': 'x' * 201}):
            self.assertEqual(self.client.get(self.path('scales'), query).status_code, 400)

    def test_partial_edits_preserve_ids_relations_and_creation_dates(self):
        for kind, row, changes in (
            ('questions', self.question, {'texto': 'Editada', 'obligatoria': False}),
            ('scales', self.scale, {'descripcion': 'Actualizada'}),
            ('options', self.option, {'etiqueta': 'Casi nunca', 'valor': -1}),
            ('ranges', self.interval, {'interpretacion': 'Descripción', 'puntaje_maximo': 8}),
        ):
            with self.subTest(kind=kind):
                created, updated = row.creado_en, row.actualizado_en
                response = self.client.patch(self.detail(kind, row.pk), changes, format='json')
                self.assertEqual(response.status_code, 200, response.data)
                row.refresh_from_db()
                self.assertEqual(row.creado_en, created)
                self.assertGreater(row.actualizado_en, updated)
                self.assertEqual(response.json()['id'], str(row.pk))
                for key, value in changes.items():
                    self.assertEqual(getattr(row, key), value)

    def test_current_uniqueness_constraints_include_inactive_records(self):
        for row in (self.question, self.scale, self.option, self.interval):
            row.activo = False
            row.save()
        for kind, changes in (
            ('questions', {'orden': 1}), ('scales', {'nombre': 'Frecuencia'}),
            ('options', {'orden': 1}), ('options', {'valor': 0}),
            ('ranges', {'orden': 1}), ('ranges', {'nombre': 'Inicial'}),
        ):
            with self.subTest(kind=kind, changes=changes):
                self.assertEqual(self.create(kind, **changes).status_code, 400)
        response = self.client.post(self.path('options', self.other_scale.pk), {'etiqueta': 'Nunca', 'orden': 1, 'valor': 0}, format='json')
        self.assertEqual(response.status_code, 201)

    def test_range_minimum_maximum_and_partial_edit_rollback(self):
        self.assertEqual(self.create('ranges', puntaje_minimo=11, puntaje_maximo=10).status_code, 400)
        response = self.create('ranges', puntaje_minimo=6, puntaje_maximo=6)
        self.assertEqual(response.status_code, 201)
        response = self.client.patch(self.detail('ranges', self.interval.pk), {'puntaje_minimo': 9, 'nombre': 'No guardar'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.interval.refresh_from_db()
        self.assertEqual(self.interval.nombre, 'Inicial')
        self.assertEqual(self.interval.puntaje_minimo, 0)

    def test_invalid_values_and_unknown_fields_do_not_write(self):
        for kind, values in (
            ('questions', {'texto': '  '}), ('questions', {'orden': 0}),
            ('questions', {'orden': 32768}), ('questions', {'orden': 1.5}),
            ('questions', {'obligatoria': 'quizas'}), ('questions', {'invertida': 'quizas'}),
            ('scales', {'nombre': ' '}), ('scales', {'nombre': 'x' * 151}),
            ('options', {'etiqueta': ''}), ('options', {'valor': 32768}),
            ('options', {'valor': -32769}), ('options', {'orden': -1}),
            ('ranges', {'nombre': ''}), ('ranges', {'puntaje_minimo': None}),
            ('ranges', {'puntaje_maximo': 2147483648}),
        ):
            with self.subTest(kind=kind, values=values):
                self.assertEqual(self.create(kind, **values).status_code, 400)
        for kind in ('questions', 'scales', 'options', 'ranges'):
            for data in ([], None, {'id': str(uuid4())}, {'deleted': True}, {'activo': False},
                         {'creado_por': 'someone'}, {'instrumento_id': str(self.other.pk)}, {'pregunta_id': str(self.question.pk)}):
                self.assertEqual(self.client.post(self.path(kind), data, format='json').status_code, 400)
        self.assertEqual(PreguntaInstrumento.objects.count(), 1)
        self.assertEqual(OpcionRespuesta.objects.count(), 1)
        self.assertEqual(RangoInterpretacion.objects.count(), 1)

    def test_reparenting_or_audit_edit_is_forbidden(self):
        for kind, row in (('questions', self.question), ('scales', self.scale), ('options', self.option), ('ranges', self.interval)):
            for values in ({'id': str(uuid4())}, {'deleted': True}, {'creado_en': '2026-01-01'}, {'activo': False}):
                self.assertEqual(self.client.patch(self.detail(kind, row.pk), values, format='json').status_code, 400)
        self.assertEqual(self.client.patch(self.detail('options', self.option.pk), {'escala_id': str(self.other_scale.pk)}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(self.detail('questions', self.question.pk), {'instrumento_id': str(self.other.pk)}, format='json').status_code, 400)

    def test_nested_urls_do_not_access_other_parents(self):
        for kind, row, parent in (('questions', self.question, self.other.pk), ('ranges', self.interval, self.other.pk), ('options', self.option, self.other_scale.pk)):
            path = self.path(kind, parent) + str(row.pk) + '/'
            self.assertEqual(self.client.get(path).status_code, 404)
            self.assertEqual(self.client.patch(path, {}, format='json').status_code, 404)
            self.assertEqual(self.client.post(path + 'deactivate/', {}, format='json').status_code, 404)
            self.assertEqual(self.client.get(self.path(kind, uuid4())).status_code, 404)
            if kind != 'ranges':
                self.assertEqual(self.client.post(path + 'move/', {'direction': 'up'}, format='json').status_code, 404)

    def test_logical_activation_never_deletes_related_data(self):
        assignment = AsignacionInstrumento.objects.create(trabajador=self.root, instrumento=self.instrument, origen='SISTEMA')
        application = AplicacionInstrumento.objects.create(asignacion=assignment)
        answer = RespuestaPregunta.objects.create(aplicacion=application, pregunta=self.question, opcion=self.option)
        for kind, row in (('questions', self.question), ('scales', self.scale), ('options', self.option), ('ranges', self.interval)):
            for action, active in (('deactivate', False), ('activate', True)):
                response = self.client.post(self.detail(kind, row.pk) + action + '/', {}, format='json')
                self.assertEqual(response.status_code, 200)
                row.refresh_from_db()
                self.assertEqual(row.activo, active)
                self.assertFalse(row.deleted)
            self.assertEqual(self.client.delete(self.detail(kind, row.pk)).status_code, 405)
            self.assertEqual(self.client.post(self.detail(kind, row.pk) + 'deactivate/', {'nombre': 'invalid'}, format='json').status_code, 400)
        answer.refresh_from_db()
        self.assertEqual(answer.opcion_id, self.option.pk)
        self.assertEqual(answer.pregunta_id, self.question.pk)

    def test_move_swaps_question_and_option_orders_without_changing_values_or_parents(self):
        for kind, row, model in (('questions', self.question, PreguntaInstrumento), ('options', self.option, OpcionRespuesta)):
            second = self.create(kind).json()
            before = row.actualizado_en
            response = self.client.post(self.detail(kind, row.pk) + 'move/', {'direction': 'down'}, format='json')
            self.assertEqual(response.status_code, 200, response.data)
            row.refresh_from_db()
            self.assertEqual(row.orden, 2)
            self.assertEqual(model.objects.get(pk=second['id']).orden, 1)
            self.assertGreater(row.actualizado_en, before)
            self.assertEqual(self.client.post(self.detail(kind, row.pk) + 'move/', {'direction': 'down'}, format='json').json()['orden'], 2)
            response = self.client.post(self.detail(kind, row.pk) + 'move/', {'direction': 'up'}, format='json')
            self.assertEqual(response.json()['orden'], 1)
            self.assertEqual(model.objects.get(pk=second['id']).orden, 2)
        self.option.refresh_from_db()
        self.assertEqual(self.option.valor, 0)

    def test_move_includes_inactive_records_and_validates_direction(self):
        row = self.create('questions').json()
        self.question.activo = False
        self.question.save()
        path = self.detail('questions', row['id']) + 'move/'
        self.assertEqual(self.client.post(path, {'direction': 'up'}, format='json').json()['orden'], 1)
        for data in ({}, {'direction': 'left'}, {'direction': 'up', 'orden': 9}):
            self.assertEqual(self.client.post(path, data, format='json').status_code, 400)

    def test_failed_reorder_rolls_back_every_position(self):
        second = self.create('questions').json()
        original_save = PreguntaInstrumento.save
        def fail_second(row, *args, **kwargs):
            if str(row.pk) == second['id']:
                raise RuntimeError('Simulated failure')
            return original_save(row, *args, **kwargs)
        with patch.object(PreguntaInstrumento, 'save', fail_second):
            with self.assertRaises(RuntimeError):
                self.client.post(self.detail('questions', self.question.pk) + 'move/', {'direction': 'down'}, format='json')
        self.question.refresh_from_db()
        self.assertEqual(self.question.orden, 1)
        self.assertEqual(PreguntaInstrumento.objects.get(pk=second['id']).orden, 2)

    def operations(self):
        for kind, row in (('questions', self.question), ('scales', self.scale), ('options', self.option), ('ranges', self.interval)):
            yield 'get', self.path(kind), {}
            yield 'post', self.path(kind), {}
            yield 'get', self.detail(kind, row.pk), {}
            yield 'patch', self.detail(kind, row.pk), {}
            for action in ('activate', 'deactivate'):
                yield 'post', self.detail(kind, row.pk) + action + '/', {}
            if kind in ('questions', 'options'):
                yield 'post', self.detail(kind, row.pk) + 'move/', {'direction': 'up'}

    def test_every_endpoint_requires_jwt(self):
        self.client.credentials()
        for method, path, data in self.operations():
            with self.subTest(method=method, path=path):
                self.assertEqual(getattr(self.client, method)(path, data, format='json').status_code, 401)

    def test_every_endpoint_requires_functional_superadmin_even_for_staff(self):
        user = get_user_model().objects.create_user(username='denied@saspel.com', is_staff=True, is_superuser=True)
        for role in ('ADMIN', 'PSICOLOGO', 'TRABAJADOR', 'NUEVO_TRABAJADOR', None):
            user.groups.set([Group.objects.get(name=role)] if role else [])
            self.authorize(user)
            for method, path, data in self.operations():
                with self.subTest(role=role, path=path):
                    self.assertEqual(getattr(self.client, method)(path, data, format='json').status_code, 403)

    def test_old_token_loses_access_after_role_removed_or_account_disabled(self):
        self.root.groups.clear()
        self.assertEqual(self.client.get(self.path('scales')).status_code, 403)
        self.root.groups.add(Group.objects.get(name='SUPERADMIN'))
        self.root.is_active = False
        self.root.save()
        self.assertEqual(self.client.get(self.path('scales')).status_code, 401)
