from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import close_old_connections, connections
from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from src.infrastructure.dependencies.responder_evaluacion import build_responder_evaluacion
from src.infrastructure.persistence.django.models import (
    AplicacionInstrumento, AsignacionInstrumento, EscalaRespuesta, InstrumentoPsicologico,
    OpcionRespuesta, PerfilUsuario, PreguntaInstrumento, RespuestaPregunta, ResultadoInstrumento,
)

User = get_user_model()
BASE = '/api/nuevo-trabajador/evaluaciones/'
DASHBOARD = '/api/nuevo-trabajador/dashboard/'


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ResponderEvaluacionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ana@saspel.com')
        self.user.groups.add(Group.objects.get(name='NUEVO_TRABAJADOR'))
        PerfilUsuario.objects.create(usuario=self.user, codigo_empleado='RESP-1')
        self.other = User.objects.create_user(username='other@saspel.com')
        self.other.groups.add(Group.objects.get(name='NUEVO_TRABAJADOR'))
        self.instrument = InstrumentoPsicologico.objects.create(
            codigo='TEST-DYNAMIC', nombre='Instrumento sintético', es_inicial=True, instrucciones='Instrucciones sintéticas.',
        )
        self.scale = EscalaRespuesta.objects.create(nombre='Escala sintética')
        self.option = OpcionRespuesta.objects.create(escala=self.scale, valor=0, orden=1, etiqueta='Opción sintética A')
        self.second = OpcionRespuesta.objects.create(escala=self.scale, valor=1, orden=2, etiqueta='Opción sintética B')
        self.questions = [PreguntaInstrumento.objects.create(
            instrumento=self.instrument, texto=f'Pregunta sintética {order}', orden=order,
            tipo_respuesta=kind, escala=self.scale if kind == 'ESCALA' else None, obligatoria=True,
        ) for order, kind in enumerate(('ESCALA', 'TEXTO', 'NUMERO', 'BOOLEANO'), 1)]
        self.assignment = AsignacionInstrumento.objects.create(trabajador=self.user, instrumento=self.instrument, origen='SISTEMA')
        self.client = APIClient()
        self.authorize(self.user)
        self.url = f'{BASE}{self.assignment.pk}/'

    def authorize(self, user):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(user)))

    def start(self):
        response = self.client.post(self.url + 'iniciar/', {}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        return response

    def answers(self):
        return [
            {'pregunta_id': str(self.questions[0].pk), 'opcion_id': str(self.option.pk)},
            {'pregunta_id': str(self.questions[1].pk), 'valor_texto': 'Texto sintético de prueba'},
            {'pregunta_id': str(self.questions[2].pk), 'valor_numerico': '0'},
            {'pregunta_id': str(self.questions[3].pk), 'valor_booleano': False},
        ]

    def send(self, answers, action='respuestas'):
        return self.client.post(self.url + action + '/', {'respuestas': answers}, format='json')

    def test_sin_preguntas_activas_no_inicia_ni_habilita_boton(self):
        PreguntaInstrumento.objects.update(activo=False)
        self.assertFalse(self.client.get(DASHBOARD).data['evaluacion_inicial']['puede_iniciar'])
        response = self.client.post(self.url + 'iniciar/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('todavía está siendo configurada', str(response.data))
        self.assertFalse(AplicacionInstrumento.objects.exists())
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.estado, 'PENDIENTE')

    def test_escala_sin_opciones_o_inactiva_bloquea_inicio(self):
        for changes in ({'activo': False}, {'activo': True, 'deleted': True}):
            EscalaRespuesta.objects.filter(pk=self.scale.pk).update(**changes)
            self.assertEqual(self.client.post(self.url + 'iniciar/', {}, format='json').status_code, 400)
        EscalaRespuesta.objects.update(activo=True, deleted=False)
        OpcionRespuesta.objects.update(activo=False)
        self.assertEqual(self.client.post(self.url + 'iniciar/', {}, format='json').status_code, 400)

    def test_inicio_idempotente_y_consulta_recuperan_misma_aplicacion(self):
        self.assertTrue(self.client.get(DASHBOARD).data['evaluacion_inicial']['puede_iniciar'])
        first = self.start().json()
        second = self.start().json()
        self.assertEqual(first, second)
        self.assertEqual(AplicacionInstrumento.objects.count(), 1)
        self.assertEqual(first['estado_asignacion'], 'EN_PROGRESO')
        self.assertEqual(first['estado_aplicacion'], 'INICIADA')
        self.assertIsNotNone(first['fecha_inicio'])
        self.assertIsNone(first['fecha_finalizacion'])
        self.assertEqual(UUID(first['asignacion_id']), self.assignment.pk)
        self.assertEqual(self.client.get(self.url).json(), first)
        app = AplicacionInstrumento.objects.get()
        self.assertEqual(app.creado_por, str(self.user.pk))
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.actualizado_por, str(self.user.pk))

    def test_contrato_dinamico_solo_preguntas_y_opciones_activas_sin_puntajes(self):
        self.second.activo = False
        self.second.save()
        PreguntaInstrumento.objects.create(instrumento=self.instrument, orden=6, texto='Oculta', tipo_respuesta='TEXTO', activo=False)
        PreguntaInstrumento.objects.create(instrumento=self.instrument, orden=7, texto='Borrada', tipo_respuesta='TEXTO', deleted=True)
        response = self.start()
        data = response.json()
        self.assertEqual([q['orden'] for q in data['preguntas']], [1, 2, 3, 4])
        self.assertEqual(data['preguntas'][0]['opciones'], [{'id': str(self.option.pk), 'etiqueta': self.option.etiqueta}])
        self.assertEqual(data['instrucciones'], 'Instrucciones sintéticas.')
        self.assertEqual(response['Cache-Control'], 'no-store')
        for question in data['preguntas']:
            self.assertEqual(set(question), {'id', 'texto', 'orden', 'tipo_respuesta', 'obligatoria', 'opciones'})
        for private in ('invertida', 'puntaje', 'rangos', 'valor":'):
            self.assertNotIn(private, response.content.decode())

    def test_guardar_parcial_actualizar_y_recuperar_sin_duplicar(self):
        self.start()
        answer = self.answers()[0]
        self.assertEqual(self.send([answer]).status_code, 200)
        row = RespuestaPregunta.objects.get()
        self.assertEqual(row.creado_por, str(self.user.pk))
        pk, created = row.pk, row.creado_en
        answer['opcion_id'] = str(self.second.pk)
        self.assertEqual(self.send([answer]).status_code, 200)
        row.refresh_from_db()
        self.assertEqual(row.opcion_id, self.second.pk)
        self.assertEqual((row.pk, row.creado_en), (pk, created))
        self.assertEqual(RespuestaPregunta.objects.count(), 1)
        detail = self.client.get(self.url).json()
        self.assertEqual(detail['respuestas'][0]['opcion_id'], str(self.second.pk))
        self.assertEqual(self.client.get(DASHBOARD).data['evaluacion_inicial']['estado'], 'EN_PROGRESO')

    def test_borrar_y_recuperar_respuesta_conserva_uuid(self):
        self.start()
        self.send([self.answers()[0]])
        pk = RespuestaPregunta.objects.get().pk
        self.assertEqual(self.send([{'pregunta_id': str(self.questions[0].pk)}]).status_code, 200)
        self.assertTrue(RespuestaPregunta.objects.get(pk=pk).deleted)
        self.assertEqual(self.client.get(self.url).json()['respuestas'], [])
        self.send([self.answers()[0]])
        self.assertEqual(RespuestaPregunta.objects.get().pk, pk)
        self.assertFalse(RespuestaPregunta.objects.get().deleted)

    def test_opcion_de_otra_escala_o_inactiva_rechazada_sin_guardado_parcial(self):
        self.start()
        scale = EscalaRespuesta.objects.create(nombre='Otra escala')
        other = OpcionRespuesta.objects.create(escala=scale, valor=0, orden=1, etiqueta='Otra')
        self.second.activo = False
        self.second.save()
        for option in (other, self.second):
            answers = [self.answers()[1], {'pregunta_id': str(self.questions[0].pk), 'opcion_id': str(option.pk)}]
            self.assertEqual(self.send(answers).status_code, 400)
            self.assertFalse(RespuestaPregunta.objects.exists())

    def test_pregunta_ajena_inactiva_o_repetida_rechazada(self):
        self.start()
        other = InstrumentoPsicologico.objects.create(codigo='OTHER', nombre='Otro')
        question = PreguntaInstrumento.objects.create(instrumento=other, texto='Ajena', orden=1, tipo_respuesta='TEXTO')
        self.assertEqual(self.send([{'pregunta_id': str(question.pk), 'valor_texto': 'No'}]).status_code, 400)
        self.assertEqual(self.send([self.answers()[0], self.answers()[0]]).status_code, 400)
        self.questions[1].activo = False
        self.questions[1].save()
        self.assertEqual(self.send([self.answers()[1]]).status_code, 400)

    def test_tipos_incompatibles_y_numeros_invalidos_rechazados(self):
        self.start()
        bad = [
            {'pregunta_id': str(self.questions[0].pk), 'valor_texto': 'No es opción'},
            {'pregunta_id': str(self.questions[1].pk), 'opcion_id': str(self.option.pk)},
            {'pregunta_id': str(self.questions[2].pk), 'valor_numerico': 'NaN'},
            {'pregunta_id': str(self.questions[2].pk), 'valor_numerico': '1.00001'},
            {'pregunta_id': str(self.questions[2].pk), 'valor_numerico': '100000000'},
            {'pregunta_id': str(self.questions[3].pk), 'valor_booleano': 'false'},
            dict(self.answers()[0], valor_booleano=True),
        ]
        for answer in bad:
            with self.subTest(answer=answer):
                self.assertEqual(self.send([answer]).status_code, 400)
        self.assertFalse(RespuestaPregunta.objects.exists())

    def test_obligatorias_impiden_finalizar_y_listan_preguntas_pendientes(self):
        self.start()
        self.send(self.answers()[:1])
        response = self.send([], 'finalizar')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['preguntas_pendientes'], [str(q.pk) for q in self.questions[1:]])
        app = AplicacionInstrumento.objects.get()
        self.assertEqual(app.estado, 'INICIADA')
        self.assertIsNone(app.fecha_finalizacion)

    def test_tipos_sin_motor_de_puntaje_no_finalizan_ni_cambian_rol(self):
        self.start()
        user_before = list(User.objects.filter(pk=self.user.pk).values())
        profile_before = list(PerfilUsuario.objects.values())
        response = self.send(self.answers(), 'finalizar')
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(AplicacionInstrumento.objects.get().estado, 'INICIADA')
        self.assertEqual(self.client.get(DASHBOARD).data['evaluacion_inicial']['estado'], 'EN_PROGRESO')
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertFalse(ResultadoInstrumento.objects.exists())
        self.assertEqual(profile_before, list(PerfilUsuario.objects.values()))
        self.assertEqual(user_before, list(User.objects.filter(pk=self.user.pk).values()))
        self.assertTrue(self.user.groups.filter(name='NUEVO_TRABAJADOR').exists())
        self.assertFalse(RespuestaPregunta.objects.exists())

    def test_opcional_vacia_no_impide_finalizar(self):
        self.questions[1].obligatoria = False
        self.questions[1].save()
        PreguntaInstrumento.objects.filter(pk__in=[q.pk for q in self.questions[2:]]).update(activo=False)
        self.start()
        answers = self.answers()[:1]
        self.assertEqual(self.send(answers, 'finalizar').status_code, 200)

    def test_no_acepta_opcion_retirada_despues_del_guardado(self):
        self.start()
        self.send(self.answers())
        self.option.activo = False
        self.option.save()
        self.assertEqual(self.send([], 'finalizar').status_code, 400)
        self.assertEqual(AplicacionInstrumento.objects.get().estado, 'INICIADA')

    def test_propiedad_rol_jwt_y_primer_acceso_en_todas_las_operaciones(self):
        self.start()
        operations = [('get', self.url, {}), ('post', self.url + 'iniciar/', {}),
                      ('post', self.url + 'respuestas/', {'respuestas': []}),
                      ('post', self.url + 'finalizar/', {'respuestas': []})]
        for condition, expected in [('other', 404), ('role', 403), ('onboarding', 403), ('anonymous', 401)]:
            self.authorize(self.user)
            self.user.groups.set([Group.objects.get(name='NUEVO_TRABAJADOR')])
            self.user.debe_cambiar_password = False
            self.user.save()
            if condition == 'other': self.authorize(self.other)
            if condition == 'role': self.user.groups.set([Group.objects.get(name='ADMIN')])
            if condition == 'onboarding':
                self.user.debe_cambiar_password = True
                self.user.save()
            if condition == 'anonymous': self.client.credentials()
            for method, url, data in operations:
                with self.subTest(condition=condition, method=method, url=url):
                    self.assertEqual(getattr(self.client, method)(url, data, format='json').status_code, expected)

    def test_no_recibe_usuario_ni_campos_internos(self):
        self.assertEqual(self.client.post(self.url + 'iniciar/', {'user_id': str(self.other.pk)}, format='json').status_code, 400)
        self.start()
        self.assertEqual(self.send([dict(self.answers()[0], invertida=True)]).status_code, 400)
        response = self.client.post(self.url + 'respuestas/', {'respuestas': [], 'usuario_id': str(self.other.pk)}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_cancelada_no_admite_inicio_guardado_ni_finalizacion(self):
        self.start()
        self.assignment.estado = 'CANCELADA'
        self.assignment.save()
        self.assertEqual(self.client.post(self.url + 'iniciar/', {}, format='json').status_code, 400)
        self.assertEqual(self.send(self.answers()).status_code, 400)
        self.assertEqual(self.send(self.answers(), 'finalizar').status_code, 400)


class InicioEvaluacionConcurrencyTests(TransactionTestCase):
    def test_inicio_concurrente_crea_una_sola_aplicacion(self):
        user = User.objects.create_user(username='concurrent-eval@saspel.com')
        instrument = InstrumentoPsicologico.objects.create(codigo='CON', nombre='Sintético', es_inicial=True)
        PreguntaInstrumento.objects.create(instrumento=instrument, texto='Texto de test', orden=1, tipo_respuesta='TEXTO')
        assignment = AsignacionInstrumento.objects.create(trabajador=user, instrumento=instrument, origen='SISTEMA')
        start = Barrier(2)

        def begin(_):
            close_old_connections()
            try:
                start.wait(timeout=10)
                return build_responder_evaluacion().iniciar(user.pk, assignment.pk).aplicacion_id
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(begin, range(2)))
        self.assertEqual(result[0], result[1])
        self.assertEqual(AplicacionInstrumento.objects.count(), 1)
