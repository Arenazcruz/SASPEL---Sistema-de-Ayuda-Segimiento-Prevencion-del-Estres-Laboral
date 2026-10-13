from io import StringIO
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from uuid import UUID

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, close_old_connections, connections, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from src.application.use_cases.evaluacion_inicial import AsignarEvaluacionInicial
from src.infrastructure.persistence.django.management.commands.seed_initial_instrument import CONFIG_PATH
from src.infrastructure.persistence.django.repositories.administration import DjangoAdministrationRepository
from src.infrastructure.persistence.django.models import (
    AplicacionInstrumento, AsignacionInstrumento, AuditableModel, EscalaRespuesta,
    InstrumentoPsicologico, OpcionRespuesta, PerfilUsuario, PreguntaInstrumento,
    RangoInterpretacion, RespuestaPregunta, ResultadoInstrumento,
)

User = get_user_model()
INSTRUMENTS = '/api/superadmin/instruments/'
USERS = '/api/superadmin/users/'
DASHBOARD = '/api/nuevo-trabajador/dashboard/'


def seed():
    call_command('seed_initial_instrument', stdout=StringIO())


class InitialInstrumentSeedTests(TestCase):
    def test_configuracion_con_diez_preguntas_y_segunda_ejecucion_identica(self):
        seed()
        instrument = InstrumentoPsicologico.objects.get(codigo='PSS10', version='1.0')
        self.assertEqual(instrument.nombre, 'Evaluación inicial de estrés laboral')
        self.assertTrue(instrument.activo and instrument.es_inicial)
        self.assertEqual(InstrumentoPsicologico.objects.filter(activo=True, es_inicial=True).count(), 1)
        scale = EscalaRespuesta.objects.get()
        questions = instrument.preguntas.order_by('orden')
        self.assertEqual(questions.count(), 10)
        self.assertEqual(list(questions.values_list('orden', flat=True)), list(range(1, 11)))
        self.assertEqual(list(questions.filter(invertida=True).values_list('orden', flat=True)), [4, 5, 7, 8])
        self.assertEqual(questions.filter(escala=scale, tipo_respuesta='ESCALA', obligatoria=True,
                                        activo=True, deleted=False).count(), 10)
        config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        self.assertEqual(list(questions.values_list('texto', flat=True)), [q['texto'] for q in config['preguntas']])
        self.assertEqual(list(scale.opciones.order_by('valor').values_list('valor', 'etiqueta')), [
            (0, 'Nunca'), (1, 'Casi nunca'), (2, 'A veces'), (3, 'A menudo'), (4, 'Muy a menudo'),
        ])
        self.assertEqual(list(instrument.rangos.order_by('orden').values_list('nombre', 'puntaje_minimo', 'puntaje_maximo')), [
            ('BAJO', 0, 13), ('MODERADO', 14, 26), ('ALTO', 27, 40),
        ])
        for item in instrument.rangos.all():
            self.assertIn('orientativa', item.interpretacion)
            self.assertIn('No constituye diagnóstico clínico', item.interpretacion)
        models = (InstrumentoPsicologico, EscalaRespuesta, OpcionRespuesta, PreguntaInstrumento, RangoInterpretacion)
        before = [list(model.objects.order_by('pk').values()) for model in models]
        seed()
        self.assertEqual(before, [list(model.objects.order_by('pk').values()) for model in models])
        self.assertFalse(AsignacionInstrumento.objects.exists())
        self.assertFalse(ResultadoInstrumento.objects.exists())
        for model in models:
            for row in model.objects.all():
                self.assertIsInstance(row, AuditableModel)
                self.assertIsInstance(row.pk, UUID)
                self.assertEqual(row.creado_por, 'SYSTEM')
                self.assertEqual(row.actualizado_por, 'SYSTEM')
                self.assertIsNotNone(row.creado_en)
                self.assertIsNotNone(row.actualizado_en)

    def test_reutiliza_escala_y_conserva_uuid(self):
        config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        scale = EscalaRespuesta.objects.create(**config['escala'])
        seed()
        self.assertEqual(EscalaRespuesta.objects.get().pk, scale.pk)
        self.assertEqual(scale.opciones.count(), 5)

    def test_actualiza_instrumento_anterior_conservando_uuid(self):
        config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        instrument = InstrumentoPsicologico.objects.create(**(config['instrumento'] | {
            'nombre': 'Escala de Estrés Percibido PSS-10',
            'instrucciones': 'Lee las instrucciones de la versión aprobada antes de responder. '
                             'El contenido de las preguntas está pendiente de carga institucional.',
        }))
        seed()
        self.assertEqual(InstrumentoPsicologico.objects.get().pk, instrument.pk)
        instrument.refresh_from_db()
        self.assertEqual(instrument.nombre, config['instrumento']['nombre'])
        self.assertEqual(instrument.instrucciones, config['instrumento']['instrucciones'])
        self.assertEqual(instrument.preguntas.count(), 10)

    def test_reactiva_pregunta_coincidente_sin_duplicarla(self):
        seed()
        question = PreguntaInstrumento.objects.get(orden=4)
        PreguntaInstrumento.objects.filter(pk=question.pk).update(activo=False, deleted=True)
        seed()
        question.refresh_from_db()
        self.assertTrue(question.activo)
        self.assertFalse(question.deleted)
        self.assertTrue(question.invertida)
        self.assertEqual(PreguntaInstrumento.objects.count(), 10)

    def test_pregunta_ajena_o_adicional_revierte_toda_la_carga(self):
        config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        instrument = InstrumentoPsicologico.objects.create(**config['instrumento'])
        question = PreguntaInstrumento.objects.create(
            instrumento=instrument, orden=10, texto='Contenido institucional distinto', tipo_respuesta='TEXTO',
        )
        for order in (10, 11):
            question.orden = order
            question.save()
            before = list(PreguntaInstrumento.objects.values())
            with self.subTest(order=order), self.assertRaises(CommandError):
                seed()
            self.assertEqual(before, list(PreguntaInstrumento.objects.values()))
            self.assertFalse(EscalaRespuesta.objects.exists())
            self.assertFalse(OpcionRespuesta.objects.exists())
            self.assertFalse(RangoInterpretacion.objects.exists())

    def test_otro_inicial_activo_bloquea_seed_sin_modificaciones(self):
        current = InstrumentoPsicologico.objects.create(codigo='OTHER', nombre='Prueba', es_inicial=True)
        with self.assertRaises(CommandError):
            seed()
        current.refresh_from_db()
        self.assertTrue(current.activo and current.es_inicial)
        self.assertEqual(InstrumentoPsicologico.objects.count(), 1)
        self.assertFalse(EscalaRespuesta.objects.exists())

    def test_seed_no_sobrescribe_contenido_configurado_ni_deja_carga_parcial(self):
        config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        scale = EscalaRespuesta.objects.create(**config['escala'])
        option = OpcionRespuesta.objects.create(escala=scale, valor=0, orden=1, etiqueta='Contenido existente')
        with self.assertRaises(CommandError):
            seed()
        self.assertFalse(InstrumentoPsicologico.objects.exists())
        option.refresh_from_db()
        self.assertEqual(option.etiqueta, 'Contenido existente')
        self.assertEqual(OpcionRespuesta.objects.count(), 1)

    def test_constraint_y_validacion_permiten_historial_inactivo(self):
        seed()
        old = InstrumentoPsicologico(codigo='PSS10', version='0.9', nombre='Versión histórica', es_inicial=True)
        with self.assertRaises(ValidationError):
            old.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            old.save()
        old.activo = False
        old.full_clean()
        old.save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            InstrumentoPsicologico.objects.filter(pk=old.pk).update(activo=True)
        old.refresh_from_db()
        self.assertFalse(old.activo)
        self.assertTrue(old.es_inicial)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class InitialInstrumentFlowTests(TestCase):
    def setUp(self):
        self.root = User.objects.create_user(username='root@saspel.com', email='root@saspel.com')
        self.root.groups.add(Group.objects.get(name='SUPERADMIN'))
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(self.root)))

    def create(self, role='NUEVO_TRABAJADOR', code='INITIAL-1'):
        return self.client.post(USERS, dict(
            first_name='Ana', last_name='Prueba', apellido_materno='', codigo_empleado=code, role=role,
            password='Temporal-segura-582!', password_confirmation='Temporal-segura-582!',
            fecha_nacimiento='1990-01-01',
        ), format='json')

    def dashboard(self, user):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(user)))
        # El primer acceso sigue siendo obligatorio; se completa su bandera solo en el fixture.
        self.assertEqual(client.get(DASHBOARD).status_code, 403)
        user.debe_cambiar_password = False
        user.save(update_fields=['debe_cambiar_password'])
        response = client.get(DASHBOARD)
        self.assertEqual(response.status_code, 200, response.data)
        return response.json()['evaluacion_inicial']

    def test_nuevo_usuario_recibe_asignacion_pendiente_sin_aplicacion_y_con_auditoria(self):
        seed()
        response = self.create()
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(pk=response.data['id'])
        assignment = AsignacionInstrumento.objects.get(trabajador=user)
        self.assertEqual(assignment.origen, 'SISTEMA')
        self.assertEqual(assignment.estado, 'PENDIENTE')
        self.assertIsNone(assignment.asignado_por_id)
        self.assertIsInstance(assignment.pk, UUID)
        self.assertEqual(assignment.creado_por, 'SYSTEM')
        self.assertEqual(assignment.actualizado_por, 'SYSTEM')
        self.assertIsNotNone(assignment.creado_en)
        self.assertIsNotNone(assignment.actualizado_en)
        self.assertTrue(user.debe_cambiar_password)
        self.assertFalse(user.perfil_usuario.tamizaje_resuelto)
        self.assertEqual(list(user.groups.values_list('name', flat=True)), ['NUEVO_TRABAJADOR'])
        data = self.dashboard(user)
        self.assertEqual(data['estado'], 'PENDIENTE')
        self.assertEqual(UUID(data['asignacion_id']), assignment.pk)
        self.assertEqual(data['nombre'], 'Evaluación inicial de estrés laboral')
        self.assertEqual(data['version'], '1.0')
        self.assertFalse(AplicacionInstrumento.objects.exists())
        self.assertFalse(ResultadoInstrumento.objects.exists())

    def test_sin_instrumento_usuario_se_crea_y_dashboard_sin_asignar(self):
        response = self.create()
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(pk=response.data['id'])
        self.assertTrue(PerfilUsuario.objects.filter(usuario=user).exists())
        self.assertEqual(self.dashboard(user)['estado'], 'SIN_ASIGNAR')
        self.assertFalse(AsignacionInstrumento.objects.exists())

    def test_dashboard_pasa_de_sin_asignar_a_pendiente_al_habilitar_y_asignar(self):
        response = self.create()
        user = User.objects.get(pk=response.data['id'])
        self.assertEqual(self.dashboard(user)['estado'], 'SIN_ASIGNAR')
        seed()
        self.assertFalse(AsignacionInstrumento.objects.exists())
        AsignarEvaluacionInicial(DjangoAdministrationRepository()).execute(user.pk, 'NUEVO_TRABAJADOR')
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(user)))
        self.assertEqual(client.get(DASHBOARD).data['evaluacion_inicial']['estado'], 'PENDIENTE')

    def test_otros_roles_no_reciben_asignacion_y_trabajador_no_se_crea_directamente(self):
        seed()
        for role in ('PSICOLOGO', 'ADMIN', 'SUPERADMIN'):
            response = self.create(role, role)
            self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(self.create('TRABAJADOR', 'WORKER').status_code, 400)
        worker = User.objects.create_user(username='worker@saspel.com')
        worker.groups.add(Group.objects.get(name='TRABAJADOR'))
        AsignarEvaluacionInicial(DjangoAdministrationRepository()).execute(worker.pk, 'TRABAJADOR')
        self.assertFalse(AsignacionInstrumento.objects.exists())

    def test_reintento_no_duplica_ni_reinicia_estado_o_auditoria(self):
        seed()
        response = self.create()
        user_id = response.data['id']
        case = AsignarEvaluacionInicial(DjangoAdministrationRepository())
        for state in ('PENDIENTE', 'EN_PROGRESO', 'COMPLETADA', 'CANCELADA'):
            AsignacionInstrumento.objects.filter(trabajador_id=user_id).update(estado=state)
            before = list(AsignacionInstrumento.objects.values())
            case.execute(user_id, 'NUEVO_TRABAJADOR')
            case.execute(user_id, 'NUEVO_TRABAJADOR')
            self.assertEqual(before, list(AsignacionInstrumento.objects.values()))

    def test_inactivo_o_borrado_no_se_asigna(self):
        seed()
        instrument = InstrumentoPsicologico.objects.get(codigo='PSS10')
        for index, changes in enumerate(({'activo': False}, {'activo': True, 'deleted': True})):
            InstrumentoPsicologico.objects.filter(pk=instrument.pk).update(**changes)
            self.assertEqual(self.create(code=f'INACTIVE-{index}').status_code, 201)
        self.assertFalse(AsignacionInstrumento.objects.exists())

    def test_fallo_de_asignacion_revierte_cuenta_perfil_y_grupos(self):
        seed()
        before_users = list(User.objects.values_list('pk', flat=True))
        with patch.object(DjangoAdministrationRepository, 'asegurar_asignacion_inicial', side_effect=IntegrityError('test')) as assign:
            response = self.create()
        assign.assert_called_once()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(before_users, list(User.objects.values_list('pk', flat=True)))
        self.assertFalse(PerfilUsuario.objects.exists())
        self.assertFalse(AsignacionInstrumento.objects.exists())

    def test_api_rechaza_segundo_inicial_en_alta_edicion_y_activacion(self):
        seed()
        response = self.client.post(INSTRUMENTS, {'codigo': 'OTHER', 'nombre': 'Prueba', 'es_inicial': True}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('es_inicial', response.data)
        other = InstrumentoPsicologico.objects.create(codigo='OTHER', nombre='Prueba')
        response = self.client.patch(f'{INSTRUMENTS}{other.pk}/', {'es_inicial': True}, format='json')
        self.assertEqual(response.status_code, 400)
        other.refresh_from_db()
        self.assertFalse(other.es_inicial)
        other.activo = False
        other.es_inicial = True
        other.save()
        self.assertEqual(self.client.post(f'{INSTRUMENTS}{other.pk}/activate/', {}, format='json').status_code, 400)
        other.refresh_from_db()
        self.assertFalse(other.activo)
        current = InstrumentoPsicologico.objects.get(codigo='PSS10')
        self.assertEqual(self.client.post(f'{INSTRUMENTS}{current.pk}/deactivate/', {}, format='json').status_code, 200)
        self.assertEqual(self.client.post(f'{INSTRUMENTS}{other.pk}/activate/', {}, format='json').status_code, 200)
        current.refresh_from_db()
        self.assertTrue(current.es_inicial)
        self.assertFalse(current.activo)

    def test_evaluacion_sembrada_inicia_guarda_continua_y_completa_diez_respuestas(self):
        seed()
        seed()
        instrument = InstrumentoPsicologico.objects.get(codigo='PSS10')
        scale = EscalaRespuesta.objects.get()
        response = self.create()
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(pk=response.data['id'])
        dashboard = self.dashboard(user)
        self.assertEqual(dashboard['estado'], 'PENDIENTE')
        self.assertTrue(dashboard['puede_iniciar'])
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(user)))
        url = f"/api/nuevo-trabajador/evaluaciones/{dashboard['asignacion_id']}/"
        response = client.post(url + 'iniciar/', {}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        detail = response.json()
        questions = list(instrument.preguntas.order_by('orden'))
        options = list(scale.opciones.order_by('valor'))
        self.assertEqual([q['texto'] for q in detail['preguntas']], [q.texto for q in questions])
        for question in detail['preguntas']:
            self.assertEqual([o['id'] for o in question['opciones']], [str(o.pk) for o in options])
        answers = [{'pregunta_id': str(q.pk), 'opcion_id': str(options[index % 5].pk)}
                   for index, q in enumerate(questions)]
        response = client.post(url + 'respuestas/', {'respuestas': answers[:5]}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(list(RespuestaPregunta.objects.order_by('pregunta__orden').values_list('opcion__valor', flat=True)),
                         [0, 1, 2, 3, 4])
        self.assertEqual(client.get(DASHBOARD).data['evaluacion_inicial']['estado'], 'EN_PROGRESO')
        resumed = APIClient()
        resumed.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(user)))
        detail = resumed.get(url).json()
        self.assertEqual(len(detail['respuestas']), 5)
        self.assertEqual(resumed.post(url + 'iniciar/', {}, format='json').json()['aplicacion_id'], detail['aplicacion_id'])
        incomplete = resumed.post(url + 'finalizar/', {'respuestas': []}, format='json')
        self.assertEqual(incomplete.status_code, 400)
        self.assertEqual(incomplete.json()['preguntas_pendientes'], [str(q.pk) for q in questions[5:]])
        profile_id = user.perfil_usuario.pk
        response = resumed.post(url + 'finalizar/', {'respuestas': answers[5:]}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(AplicacionInstrumento.objects.get().estado, 'FINALIZADA')
        self.assertEqual(RespuestaPregunta.objects.count(), 10)
        self.assertEqual(AsignacionInstrumento.objects.get(trabajador=user).estado, 'COMPLETADA')
        self.assertEqual(resumed.get(DASHBOARD).status_code, 403)
        self.assertEqual(ResultadoInstrumento.objects.count(), 1)
        self.assertEqual(list(user.groups.values_list('name', flat=True)), ['TRABAJADOR'])
        self.assertTrue(PerfilUsuario.objects.get(pk=profile_id).tamizaje_resuelto)
        before = list(RespuestaPregunta.objects.order_by('pk').values())
        for action in ('iniciar', 'respuestas'):
            payload = {} if action == 'iniciar' else {'respuestas': answers}
            self.assertEqual(resumed.post(url + action + '/', payload, format='json').status_code, 403)
        self.assertEqual(resumed.post(url + 'finalizar/', {'respuestas': answers}, format='json').json(), response.json())
        seed()
        self.assertEqual(before, list(RespuestaPregunta.objects.order_by('pk').values()))
        self.assertEqual(AplicacionInstrumento.objects.count(), 1)


class InitialAssignmentConcurrencyTests(TransactionTestCase):
    def test_reintentos_concurrentes_generan_una_sola_asignacion(self):
        Group.objects.get_or_create(name='SUPERADMIN')
        group, _ = Group.objects.get_or_create(name='NUEVO_TRABAJADOR')
        seed()
        user = User.objects.create_user(username='concurrent@saspel.com')
        user.groups.add(group)
        PerfilUsuario.objects.create(usuario=user, codigo_empleado='CONCURRENT-INITIAL')
        start = Barrier(2)

        def assign(_):
            close_old_connections()
            try:
                start.wait(timeout=10)
                AsignarEvaluacionInicial(DjangoAdministrationRepository()).execute(user.pk, 'NUEVO_TRABAJADOR')
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(assign, range(2)))
        self.assertEqual(AsignacionInstrumento.objects.filter(trabajador=user).count(), 1)
