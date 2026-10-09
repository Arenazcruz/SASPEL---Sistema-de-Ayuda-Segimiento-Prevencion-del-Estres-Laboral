"""UUID y auditoría sobre el esquema PostgreSQL creado por las migraciones de pruebas."""

from datetime import time, timedelta
from unittest.mock import patch
from uuid import UUID, uuid4

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import connection, models
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from src.infrastructure.persistence.django.models import (
    AplicacionInstrumento, AreaInstitucional, AsignacionInstrumento,
    AsignacionProfesional, AuditableModel, CargoInstitucional, Cita,
    DisponibilidadPsicologo, EscalaRespuesta, InstrumentoPsicologico,
    OpcionRespuesta, PerfilUsuario, PreguntaInstrumento, RangoInterpretacion,
    RespuestaPregunta, ResultadoInstrumento, Usuario,
)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class UUIDAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.started = timezone.now()
        cls.user = Usuario.objects.create_user(
            username='audit@saspel.com', email='audit@saspel.com', password='Prueba-UUID-876!',
        )
        cls.user.groups.add(Group.objects.get(name='SUPERADMIN'))
        cls.psychologist = Usuario.objects.create_user(username='psychologist@saspel.com')
        area = AreaInstitucional.objects.create(nombre='Área de prueba')
        cargo = CargoInstitucional.objects.create(nombre='Cargo de prueba')
        profile = PerfilUsuario.objects.create(
            usuario=cls.user, codigo_empleado='UUID-1', area=area, cargo=cargo,
        )
        professional = AsignacionProfesional.objects.create(
            trabajador=cls.user, psicologo=cls.psychologist,
        )
        instrument = InstrumentoPsicologico.objects.create(codigo='UUID', nombre='Prueba UUID')
        scale = EscalaRespuesta.objects.create(nombre='Escala de prueba')
        option = OpcionRespuesta.objects.create(escala=scale, etiqueta='Opción', valor=1, orden=1)
        question = PreguntaInstrumento.objects.create(
            instrumento=instrument, escala=scale, texto='Pregunta de prueba', orden=1,
            tipo_respuesta='ESCALA',
        )
        interval = RangoInterpretacion.objects.create(
            instrumento=instrument, nombre='Rango de prueba', puntaje_minimo=0,
            puntaje_maximo=10, orden=1,
        )
        assignment = AsignacionInstrumento.objects.create(
            trabajador=cls.user, instrumento=instrument, asignado_por=cls.psychologist,
            origen='PROFESIONAL',
        )
        application = AplicacionInstrumento.objects.create(asignacion=assignment)
        answer = RespuestaPregunta.objects.create(aplicacion=application, pregunta=question, opcion=option)
        result = ResultadoInstrumento.objects.create(
            aplicacion=application, rango=interval, puntaje_total=1, fecha_calculo=timezone.now(),
        )
        availability = DisponibilidadPsicologo.objects.create(
            psicologo=cls.psychologist, dia_semana=0, hora_inicio=time(8), hora_fin=time(12),
        )
        appointment = Cita.objects.create(
            trabajador=cls.user, psicologo=cls.psychologist, solicitada_por=cls.user,
            fecha_inicio=timezone.now(), fecha_fin=timezone.now() + timedelta(hours=1),
            motivo='Prueba UUID',
        )
        cls.records = [cls.user, area, cargo, profile, professional, instrument, scale, option,
                       question, interval, assignment, application, answer, result, availability, appointment]

    def test_all_sixteen_entities_persist_generated_uuid_primary_keys(self):
        registered = set(apps.get_app_config('api').get_models())
        self.assertEqual(registered, {type(row) for row in self.records})
        self.assertEqual(len(registered), 16)
        self.assertTrue(AuditableModel._meta.abstract)
        ids = set()
        for row in self.records:
            with self.subTest(model=type(row).__name__):
                self.assertIsInstance(row, AuditableModel)
                self.assertIsInstance(row._meta.pk, models.UUIDField)
                self.assertFalse(row._meta.pk.editable)
                original = row.pk
                row.refresh_from_db()
                self.assertIsInstance(row.pk, UUID)
                self.assertEqual(row.pk, original)
                self.assertEqual(row.pk.version, 4)
                ids.add(row.pk)
        self.assertEqual(len(ids), 16)

    def test_uuid_foreign_keys_round_trip_for_every_entity(self):
        for row in self.records:
            for field in row._meta.fields:
                if not isinstance(field, models.ForeignKey):
                    continue
                with self.subTest(model=type(row).__name__, field=field.name):
                    self.assertIsInstance(field.target_field, models.UUIDField)
                    related_id = getattr(row, field.attname)
                    if related_id is not None:
                        self.assertIsInstance(related_id, UUID)
                        self.assertEqual(getattr(row, field.name).pk, related_id)
        original = self.records[-1]
        followup = Cita.objects.create(
            trabajador=self.user, psicologo=self.psychologist, solicitada_por=self.user,
            fecha_inicio=original.fecha_inicio + timedelta(days=1),
            fecha_fin=original.fecha_fin + timedelta(days=1), motivo='Cambio', cita_origen=original,
        )
        followup.refresh_from_db()
        self.assertEqual(followup.cita_origen_id, original.pk)

    def test_audit_columns_defaults_and_automatic_creation_on_all_entities(self):
        expected = {'creado_en': 'Time_Create', 'actualizado_en': 'Time_Update',
                    'creado_por': 'User_Create', 'actualizado_por': 'User_Update'}
        for row in self.records:
            with self.subTest(model=type(row).__name__):
                row.refresh_from_db()
                self.assertGreaterEqual(row.creado_en, self.started)
                self.assertGreaterEqual(row.actualizado_en, row.creado_en)
                self.assertEqual(row.creado_por, 'SYSTEM')
                self.assertEqual(row.actualizado_por, 'SYSTEM')
                self.assertIs(row.deleted, False)
                with connection.cursor() as cursor:
                    columns = {column.name for column in connection.introspection.get_table_description(
                        cursor, row._meta.db_table,
                    )}
                for field, column in expected.items():
                    self.assertEqual(row._meta.get_field(field).column, column)
                    self.assertIn(column, columns)
                self.assertIn('deleted', columns)

    def test_full_and_partial_saves_update_time_but_preserve_creation(self):
        future = timezone.now() + timedelta(days=1)
        for row in self.records:
            with self.subTest(model=type(row).__name__):
                created = row.creado_en
                row.creado_por = 'IMPORT'
                with patch('django.utils.timezone.now', return_value=future):
                    row.save()
                row.refresh_from_db()
                self.assertEqual(row.actualizado_en, future)
                self.assertEqual(row.creado_en, created)
                row.actualizado_por = str(self.psychologist.pk)
                with patch('django.utils.timezone.now', return_value=future + timedelta(hours=1)):
                    row.save(update_fields=['actualizado_por'])
                row.refresh_from_db()
                self.assertEqual(row.actualizado_en, future + timedelta(hours=1))
                self.assertEqual(row.creado_en, created)
                self.assertEqual(row.creado_por, 'IMPORT')
                self.assertEqual(row.actualizado_por, str(self.psychologist.pk))

    def test_empty_update_fields_remains_a_noop(self):
        before = self.user.actualizado_en
        self.user.deleted = True
        self.user.save(update_fields=[])
        self.user.refresh_from_db()
        self.assertFalse(self.user.deleted)
        self.assertEqual(self.user.actualizado_en, before)

    def test_deleted_is_independent_of_existing_business_states(self):
        for row in self.records:
            with self.subTest(model=type(row).__name__):
                previous = {name: getattr(row, name) for name in ('activo', 'is_active', 'estado')
                            if hasattr(row, name)}
                row.deleted = True
                row.save(update_fields=['deleted'])
                row.refresh_from_db()
                self.assertTrue(row.deleted)
                for name, value in previous.items():
                    self.assertEqual(getattr(row, name), value)

    def test_custom_user_retains_django_groups_permissions_and_passwords(self):
        self.assertIs(get_user_model(), Usuario)
        self.assertEqual(settings.AUTH_USER_MODEL, 'api.Usuario')
        self.assertIsInstance(self.user, AbstractUser)
        self.assertTrue(self.user.check_password('Prueba-UUID-876!'))
        self.assertEqual(set(Group.objects.values_list('name', flat=True)),
                         {'SUPERADMIN', 'ADMIN', 'PSICOLOGO', 'TRABAJADOR', 'NUEVO_TRABAJADOR'})
        permission = Permission.objects.get(content_type__app_label='api', codename='view_usuario')
        self.user.user_permissions.add(permission)
        self.assertTrue(self.user.has_perm('api.view_usuario'))
        # Los modelos internos Django conservan sus claves originales.
        self.assertNotIsInstance(Group._meta.pk, models.UUIDField)
        self.assertNotIsInstance(Permission._meta.pk, models.UUIDField)

    def test_login_refresh_and_json_ids_preserve_uuid(self):
        client = APIClient()
        response = client.post('/api/auth/login/', {
            'email': self.user.email, 'password': 'Prueba-UUID-876!',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['user']['id'], str(self.user.pk))
        self.assertEqual(AccessToken(body['access'])['user_id'], str(self.user.pk))
        refreshed = client.post('/api/auth/refresh/', {'refresh': body['refresh']}, format='json')
        self.assertEqual(refreshed.status_code, 200)
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + refreshed.json()['access'])
        self.assertEqual(client.get('/api/auth/me/').json()['id'], str(self.user.pk))
        for endpoint, expected in (
            (f'users/{self.user.pk}/', self.user.pk),
            (f'areas/{self.records[1].pk}/', self.records[1].pk),
            (f'cargos/{self.records[2].pk}/', self.records[2].pk),
            (f'instruments/{self.records[5].pk}/', self.records[5].pk),
        ):
            with self.subTest(endpoint=endpoint):
                response = client.get('/api/superadmin/' + endpoint)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['id'], str(expected))
        assignment = client.get('/api/superadmin/assignments/').json()['results'][0]
        self.assertEqual(assignment['id'], str(self.records[4].pk))
        self.assertEqual(assignment['trabajador']['id'], str(self.user.pk))
        self.assertEqual(assignment['psicologo']['id'], str(self.psychologist.pk))

    def test_old_or_malformed_jwt_identity_returns_401_instead_of_500(self):
        client = APIClient()
        for value in (1, '1', 'invalid-uuid', None, {}, str(uuid4())):
            with self.subTest(value=value):
                access, refresh = AccessToken.for_user(self.user), RefreshToken.for_user(self.user)
                access['user_id'] = refresh['user_id'] = value
                client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(access))
                for path in ('/api/auth/me/', '/api/superadmin/users/'):
                    self.assertEqual(client.get(path).status_code, 401)
                self.assertEqual(client.post('/api/auth/refresh/', {'refresh': str(refresh)},
                                             format='json').status_code, 401)

    def test_invalid_uuid_inputs_and_routes_are_rejected(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(self.user)))
        for value in ('1', 'invalid-uuid'):
            with self.subTest(value=value):
                self.assertEqual(client.get('/api/superadmin/users/', {'area': value}).status_code, 400)
                self.assertEqual(client.get('/api/superadmin/users/', {'cargo': value}).status_code, 400)
                self.assertEqual(client.post('/api/superadmin/assignments/', {
                    'trabajador_id': value, 'psicologo_id': str(self.psychologist.pk),
                }, format='json').status_code, 400)
                self.assertEqual(client.patch(f'/api/superadmin/users/{self.user.pk}/', {
                    'area_id': value,
                }, format='json').status_code, 400)
                for resource in ('users', 'areas', 'cargos', 'instruments'):
                    self.assertEqual(client.get(f'/api/superadmin/{resource}/{value}/').status_code, 404)
