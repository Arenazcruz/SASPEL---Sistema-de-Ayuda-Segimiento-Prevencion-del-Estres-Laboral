"""T25-A: HTTP, JWT y persistencia real del catálogo existente, en BD temporal."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from src.infrastructure.persistence.django.models import InstrumentoPsicologico, PreguntaInstrumento

BASE = '/api/superadmin/instruments/'


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class InstrumentsApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = get_user_model().objects.create_user(username='root@saspel.com')
        cls.root.groups.add(Group.objects.get(name='SUPERADMIN'))
        cls.item = InstrumentoPsicologico.objects.create(codigo='TEST-A', nombre='Instrumento ficticio', es_inicial=True)
        cls.other = InstrumentoPsicologico.objects.create(codigo='TEST-A', version='2.0', nombre='Otra versión', activo=False)

    def setUp(self):
        self.client = APIClient()
        self.authorize(self.root)

    def authorize(self, user):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(user)))

    def create(self, **changes):
        return self.client.post(BASE, {'codigo': 'TEST-NUEVO', 'nombre': 'Prueba ficticia'} | changes, format='json')

    def test_list_and_detail_include_existing_fields(self):
        response = self.client.get(BASE)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['page_size'], 20)
        self.assertEqual([row['id'] for row in response.data['results']], [self.item.pk, self.other.pk])
        detail = self.client.get(f'{BASE}{self.item.pk}/')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(set(detail.data), {'id', 'codigo', 'nombre', 'version', 'descripcion', 'instrucciones',
                                           'es_inicial', 'activo', 'creado_en', 'actualizado_en'})
        self.assertEqual(detail['Cache-Control'], 'no-store')

    def test_search_and_combined_filters(self):
        for query, ids in (
            ({'search': 'ficticio'}, [self.item.pk]),
            ({'search': 'test-a'}, [self.item.pk, self.other.pk]),
            ({'search': '2.0'}, [self.other.pk]),
            ({'activo': 'true', 'es_inicial': 'true'}, [self.item.pk]),
            ({'activo': 'false', 'es_inicial': 'false'}, [self.other.pk]),
            ({'activo': 'true', 'search': '2.0'}, []),
            ({'search': "' OR 1=1 --"}, []),
        ):
            with self.subTest(query=query):
                response = self.client.get(BASE, query)
                self.assertEqual(response.status_code, 200)
                self.assertEqual([row['id'] for row in response.data['results']], ids)

    def test_pagination_is_stable_and_bounded(self):
        InstrumentoPsicologico.objects.bulk_create([
            InstrumentoPsicologico(codigo=f'PAGE-{index:02}', nombre='Prueba') for index in range(22)
        ])
        first = self.client.get(BASE).data
        second = self.client.get(BASE, {'page': 2}).data
        self.assertEqual((first['count'], len(first['results']), len(second['results'])), (24, 20, 4))
        self.assertFalse({row['id'] for row in first['results']} & {row['id'] for row in second['results']})
        self.assertEqual(self.client.get(BASE, {'page': 999}).data['results'], [])

    def test_invalid_filters(self):
        for query in ({'page': 0}, {'page': 'abc'}, {'activo': 'quizá'}, {'es_inicial': 'quizá'}, {'search': 'x' * 201}):
            with self.subTest(query=query):
                self.assertEqual(self.client.get(BASE, query).status_code, 400)

    def test_create_defaults_and_full_metadata(self):
        response = self.create()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['version'], '1.0')
        self.assertTrue(response.data['activo'])
        self.assertFalse(response.data['es_inicial'])
        self.assertEqual(response.data['instrucciones'], '')
        full = self.create(codigo='  TEST-FULL  ', version='2.1', nombre=' Prueba completa ',
                           descripcion='Descripción', instrucciones='Primera línea\nSegunda línea', es_inicial=True)
        self.assertEqual(full.status_code, 201)
        saved = InstrumentoPsicologico.objects.get(pk=full.data['id'])
        self.assertEqual(saved.codigo, 'TEST-FULL')
        self.assertEqual(saved.nombre, 'Prueba completa')
        self.assertEqual(saved.instrucciones, 'Primera línea\nSegunda línea')
        self.assertTrue(saved.es_inicial)

    def test_create_validations_and_no_extra_fields(self):
        for changes in ({'codigo': ''}, {'codigo': '  '}, {'codigo': 'x' * 51}, {'nombre': ' '},
                        {'nombre': 'x' * 201}, {'version': ''}, {'version': 'x' * 51},
                        {'es_inicial': 'quizá'}, {'descripcion': None}, {'activo': False},
                        {'creado_en': '2026-01-01'}, {'preguntas': []}, {'id': 90}):
            with self.subTest(changes=changes):
                response = self.create(**changes)
                self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(self.client.post(BASE, {}, format='json').status_code, 400)
        self.assertEqual(self.client.post(BASE, [], format='json').status_code, 400)
        self.assertEqual(InstrumentoPsicologico.objects.count(), 2)

    def test_uniqueness_includes_inactive_versions_and_allows_different_version(self):
        for version in ('1.0', '2.0'):
            response = self.create(codigo='TEST-A', version=version)
            self.assertEqual(response.status_code, 400, response.data)
            self.assertIn('version', response.data)
        self.assertEqual(self.create(codigo='TEST-A', version='3.0').status_code, 201)
        self.assertEqual(self.create(codigo='OTHER', version='1.0').status_code, 201)

    def test_edit_partial_preserves_unsupplied_fields_and_timestamps(self):
        created = self.other.creado_en
        response = self.client.patch(f'{BASE}{self.other.pk}/', {'nombre': 'Editado', 'descripcion': 'Texto'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.other.refresh_from_db()
        self.assertEqual(self.other.nombre, 'Editado')
        self.assertEqual(self.other.version, '2.0')
        self.assertFalse(self.other.activo)
        self.assertEqual(self.other.creado_en, created)
        self.assertGreater(self.other.actualizado_en, created)
        response = self.client.patch(f'{BASE}{self.other.pk}/', {'codigo': 'UPDATED', 'version': '3',
            'instrucciones': 'Lee con atención', 'es_inicial': True}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['es_inicial'])

    def test_conflicting_edit_rolls_back_all_changes(self):
        response = self.client.patch(f'{BASE}{self.other.pk}/', {'version': '1.0', 'nombre': 'No guardar'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.other.refresh_from_db()
        self.assertEqual(self.other.version, '2.0')
        self.assertEqual(self.other.nombre, 'Otra versión')
        self.assertEqual(self.client.patch(f'{BASE}{self.item.pk}/', {'version': '1.0'}, format='json').status_code, 200)

    def test_edit_rejects_invalid_fields_and_direct_state_change(self):
        for data in ({'nombre': ''}, {'version': None}, {'codigo': 'x' * 51}, {'activo': False}, {'actualizado_en': '2026-01-01'}):
            self.assertEqual(self.client.patch(f'{BASE}{self.item.pk}/', data, format='json').status_code, 400)

    def test_activation_is_reversible_and_never_deletes_related_records(self):
        question = PreguntaInstrumento.objects.create(instrumento=self.item, texto='Prueba', orden=1, tipo_respuesta='TEXTO')
        for action, active in (('deactivate', False), ('deactivate', False), ('activate', True)):
            response = self.client.post(f'{BASE}{self.item.pk}/{action}/', {}, format='json')
            self.assertEqual(response.status_code, 200)
            self.item.refresh_from_db()
            self.assertEqual(self.item.activo, active)
            self.assertEqual(response.data['activo'], active)
            question.refresh_from_db()
            self.assertEqual(question.instrumento_id, self.item.pk)
        self.assertEqual(InstrumentoPsicologico.objects.count(), 2)
        self.assertEqual(self.client.delete(f'{BASE}{self.item.pk}/').status_code, 405)
        self.assertTrue(InstrumentoPsicologico.objects.filter(pk=self.item.pk).exists())
        self.assertEqual(self.client.post(f'{BASE}{self.item.pk}/deactivate/', {'nombre': 'No'}, format='json').status_code, 400)

    def test_missing_instrument_returns_404(self):
        for method, suffix in (('get', ''), ('patch', ''), ('post', 'activate/'), ('post', 'deactivate/')):
            response = getattr(self.client, method)(f'{BASE}00000000-0000-0000-0000-000000999999/{suffix}', {}, format='json')
            self.assertEqual(response.status_code, 404)

    def requests(self):
        return [('get', BASE), ('post', BASE), ('get', f'{BASE}{self.item.pk}/'),
                ('patch', f'{BASE}{self.item.pk}/'), ('post', f'{BASE}{self.item.pk}/activate/'),
                ('post', f'{BASE}{self.item.pk}/deactivate/')]

    def test_every_operation_requires_jwt(self):
        self.client.credentials()
        for method, url in self.requests():
            with self.subTest(method=method, url=url):
                self.assertEqual(getattr(self.client, method)(url, {}, format='json').status_code, 401)

    def test_every_operation_rejects_other_roles_even_with_staff_flags(self):
        user = get_user_model().objects.create_user(username='other@saspel.com', is_staff=True, is_superuser=True)
        for role in ('ADMIN', 'PSICOLOGO', 'TRABAJADOR', 'NUEVO_TRABAJADOR', None):
            user.groups.set([Group.objects.get(name=role)] if role else [])
            self.authorize(user)
            for method, url in self.requests():
                with self.subTest(role=role, method=method, url=url):
                    self.assertEqual(getattr(self.client, method)(url, {}, format='json').status_code, 403)

    def test_existing_token_loses_access_after_role_or_active_change(self):
        self.root.groups.clear()
        self.assertEqual(self.client.get(BASE).status_code, 403)
        self.root.groups.add(Group.objects.get(name='SUPERADMIN'))
        self.root.is_active = False
        self.root.save(update_fields=['is_active'])
        self.assertEqual(self.client.get(BASE).status_code, 401)
