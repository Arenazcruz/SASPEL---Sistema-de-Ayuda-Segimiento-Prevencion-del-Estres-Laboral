from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from io import StringIO
from threading import Barrier
from unittest.mock import patch
from uuid import UUID, uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import close_old_connections, connections
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from src.application.dto.responder_evaluacion import RespuestaEvaluacion
from src.domain.exceptions.evaluacion import EvaluacionError
from src.domain.services.resultado_evaluacion import ItemPuntaje, RangoPuntaje, calcular_puntaje, seleccionar_rango
from src.infrastructure.dependencies.responder_evaluacion import build_responder_evaluacion
from src.infrastructure.persistence.django.models import (
    AceptacionPolitica, AplicacionInstrumento, AsignacionInstrumento, AsignacionProfesional,
    InstrumentoPsicologico, PerfilUsuario, PoliticaSistema, RangoInterpretacion,
    RespuestaPregunta, ResultadoInstrumento,
)
from src.infrastructure.persistence.django.repositories.responder_evaluacion import DjangoResponderEvaluacionRepository
from src.infrastructure.persistence.django.repositories.assignments import DjangoAssignmentRepository

User = get_user_model()
RESULT_URL = '/api/trabajador/evaluacion-inicial/resultado/'


class CalculoTests(SimpleTestCase):
    def test_suma_e_inversion_generica(self):
        values = tuple(map(Decimal, ('2', '3', '4', '5', '6')))
        self.assertEqual(calcular_puntaje((ItemPuntaje('ESCALA', False, Decimal(3), values),
                                         ItemPuntaje('ESCALA', True, Decimal(2), values))), Decimal(9))

    def test_minimo_maximo_e_inversion_actual(self):
        values = tuple(Decimal(v) for v in range(5))
        for selected in range(5):
            self.assertEqual(calcular_puntaje((ItemPuntaje('ESCALA', True, Decimal(selected), values),)), 4-selected)
        for expected in (0, 40):
            items = tuple(ItemPuntaje('ESCALA', order in (4, 5, 7, 8),
                                     Decimal((4 if order in (4, 5, 7, 8) else 0) if expected == 0
                                             else (0 if order in (4, 5, 7, 8) else 4)), values)
                          for order in range(1, 11))
            self.assertEqual(calcular_puntaje(items), expected)

    def test_rangos_limites_sin_rango_y_solapados(self):
        ranges = tuple(RangoPuntaje(uuid4(), Decimal(low), Decimal(high)) for low, high in ((0, 13), (14, 26), (27, 40)))
        for score, index in ((0, 0), (13, 0), (14, 1), (26, 1), (27, 2), (40, 2)):
            self.assertEqual(seleccionar_rango(Decimal(score), ranges), ranges[index].id)
        self.assertIsNone(seleccionar_rango(Decimal(41), ranges))
        with self.assertRaises(EvaluacionError):
            seleccionar_rango(Decimal(10), ranges + (RangoPuntaje(uuid4(), Decimal(0), Decimal(20)),))

    def test_configuracion_no_calculable(self):
        for items in ((), (ItemPuntaje('TEXTO', False, Decimal(0), (Decimal(0),)),),
                      (ItemPuntaje('ESCALA', False, Decimal(5), (Decimal(0), Decimal(4))),)):
            with self.subTest(items=items), self.assertRaises(EvaluacionError):
                calcular_puntaje(items)


class CierreFixture:
    def person(self, name, role='NUEVO_TRABAJADOR', **changes):
        user = User.objects.create_user(username=f'{name}@saspel.com', email=f'{name}@saspel.com', **changes)
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)
        PerfilUsuario.objects.create(usuario=user, codigo_empleado=name)
        return user

    def prepare(self):
        for name in ('SUPERADMIN', 'NUEVO_TRABAJADOR', 'TRABAJADOR', 'PSICOLOGO', 'ADMIN'):
            Group.objects.get_or_create(name=name)
        call_command('seed_initial_instrument', stdout=StringIO())
        self.user = self.person('cierre')
        self.instrument = InstrumentoPsicologico.objects.get(es_inicial=True)
        self.assignment = AsignacionInstrumento.objects.create(trabajador=self.user, instrumento=self.instrument, origen='SISTEMA')
        self.case = build_responder_evaluacion()
        self.case.iniciar(self.user.pk, self.assignment.pk)
        self.url = f'/api/nuevo-trabajador/evaluaciones/{self.assignment.pk}/finalizar/'
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(self.user)))

    def answers(self, total=20):
        remaining = total
        answers = []
        for question in self.instrument.preguntas.order_by('orden'):
            contribution = min(remaining, 4)
            remaining -= contribution
            value = 4-contribution if question.invertida else contribution
            answers.append({'pregunta_id': str(question.pk), 'opcion_id': str(question.escala.opciones.get(valor=value).pk)})
        return answers

    def finish(self, total=20):
        return self.client.post(self.url, {'respuestas': self.answers(total)}, format='json')


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CierreOnboardingTests(CierreFixture, TestCase):
    def setUp(self):
        self.prepare()

    def assert_rollback(self):
        self.assertFalse(ResultadoInstrumento.objects.exists())
        self.assertFalse(AsignacionProfesional.objects.exists())
        self.assertFalse(RespuestaPregunta.objects.exists())
        self.assertEqual(AplicacionInstrumento.objects.get().estado, 'INICIADA')
        self.assertIsNone(AplicacionInstrumento.objects.get().fecha_finalizacion)
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.estado, 'EN_PROGRESO')
        self.assertFalse(PerfilUsuario.objects.get(usuario=self.user).tamizaje_resuelto)
        self.assertEqual(list(self.user.groups.values_list('name', flat=True)), ['NUEVO_TRABAJADOR'])

    def test_resultado_transicion_auditoria_identidad_politicas_y_retry(self):
        policy = PoliticaSistema.objects.create(tipo='TERMINOS_USO', titulo='Condiciones', version='test', contenido='Texto')
        AceptacionPolitica.objects.create(usuario=self.user, politica=policy)
        policies_before = list(AceptacionPolitica.objects.values())
        fields = ('id', 'email', 'password', 'is_staff', 'is_superuser', 'creado_en', 'creado_por')
        user_before = User.objects.values(*fields).get(pk=self.user.pk)
        profile = PerfilUsuario.objects.get(usuario=self.user)
        profile_before = {k: v for k, v in profile.__dict__.items() if k not in ('_state', 'tamizaje_resuelto', 'actualizado_en', 'actualizado_por')}
        # Guardar primero permite comprobar que finalizar no cambia respuestas persistidas.
        saved = self.client.post(self.url.replace('finalizar/', 'respuestas/'), {'respuestas': self.answers()}, format='json')
        self.assertEqual(saved.status_code, 200)
        values_before = list(RespuestaPregunta.objects.order_by('pk').values())
        response = self.client.post(self.url, {'respuestas': []}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        result = ResultadoInstrumento.objects.get()
        self.assertEqual(result.puntaje_total, 20)
        self.assertEqual(result.rango.nombre, 'MODERADO')
        self.assertIsInstance(result.pk, UUID)
        self.assertIsNotNone(result.fecha_calculo)
        self.assertIsNotNone(result.creado_en)
        self.assertIsNotNone(result.actualizado_en)
        self.assertFalse(result.deleted)
        self.assertEqual(result.creado_por, str(self.user.pk))
        self.assertEqual(result.actualizado_por, str(self.user.pk))
        self.assertEqual(values_before, list(RespuestaPregunta.objects.order_by('pk').values()))
        self.assertEqual(user_before, User.objects.values(*fields).get(pk=self.user.pk))
        profile.refresh_from_db()
        self.assertTrue(profile.tamizaje_resuelto)
        self.assertEqual(profile_before, {k: v for k, v in profile.__dict__.items() if k in profile_before})
        self.assertEqual(policies_before, list(AceptacionPolitica.objects.values()))
        self.assertEqual(list(self.user.groups.values_list('name', flat=True)), ['TRABAJADOR'])
        self.assertEqual(response.data['nuevo_rol'], 'TRABAJADOR')
        self.assertEqual(response.data['estado_asignacion_profesional'], 'PENDIENTE')
        identity = self.client.get('/api/auth/me/')
        self.assertEqual(identity.status_code, 200)
        self.assertEqual(identity.data['role'], 'TRABAJADOR')
        self.assertEqual(identity.data['dashboard_path'], '/dashboard/trabajador')
        before = [list(m.objects.order_by('pk').values()) for m in (ResultadoInstrumento, PerfilUsuario, User, RespuestaPregunta)]
        retry = self.finish(40)
        self.assertEqual(retry.json(), response.json())
        self.assertEqual(before, [list(m.objects.order_by('pk').values()) for m in (ResultadoInstrumento, PerfilUsuario, User, RespuestaPregunta)])
        self.assertEqual(self.client.get(RESULT_URL).json(), response.json())

    def test_puntajes_y_rangos_desde_bd(self):
        for total, name in ((0, 'BAJO'), (13, 'BAJO'), (14, 'MODERADO'), (26, 'MODERADO'), (27, 'ALTO'), (40, 'ALTO')):
            with self.subTest(total=total):
                user = self.person(f'limite-{total}')
                assignment = AsignacionInstrumento.objects.create(trabajador=user, instrumento=self.instrument, origen='SISTEMA')
                self.case.iniciar(user.pk, assignment.pk)
                answers = tuple(RespuestaEvaluacion(UUID(a['pregunta_id']), UUID(a['opcion_id'])) for a in self.answers(total))
                result = self.case.finalizar(user.pk, assignment.pk, answers)
                self.assertEqual(Decimal(result.puntaje_total), total)
                self.assertEqual(result.rango, name)

    def test_sin_rango_no_inventa_clasificacion(self):
        self.instrument.rangos.update(activo=False)
        response = self.finish()
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIsNone(response.data['rango'])
        self.assertEqual(response.data['interpretacion'], '')
        self.assertIsNone(ResultadoInstrumento.objects.get().rango_id)

    def test_rango_personalizado_y_rango_eliminado_ignorado(self):
        self.instrument.rangos.filter(nombre='MODERADO').update(nombre='ORIENTATIVO', interpretacion='Texto configurado')
        RangoInterpretacion.objects.create(instrumento=self.instrument, nombre='Oculto', orden=4,
                                          puntaje_minimo=0, puntaje_maximo=40, deleted=True)
        response = self.finish()
        self.assertEqual(response.data['rango'], 'ORIENTATIVO')
        self.assertEqual(response.data['interpretacion'], 'Texto configurado')

    def test_solapamiento_revierte_incluso_guardado_de_respuestas(self):
        RangoInterpretacion.objects.create(instrumento=self.instrument, nombre='Solapado', orden=4,
                                          puntaje_minimo=0, puntaje_maximo=40)
        response = self.finish()
        self.assertEqual(response.status_code, 400)
        self.assertIn('rangos', response.data['detail'])
        self.assert_rollback()

    def test_fallos_criticos_y_de_calculo_revierten_todo(self):
        for target, method in ((DjangoResponderEvaluacionRepository, 'datos_calculo'),
                               (DjangoResponderEvaluacionRepository, 'completar_onboarding'),
                               (DjangoAssignmentRepository, 'create_assignment')):
            if method == 'create_assignment':
                self.person('professional', 'PSICOLOGO')
            with self.subTest(method=method), patch.object(target, method, side_effect=EvaluacionError('Fallo crítico')):
                self.assertEqual(self.finish().status_code, 400)
            self.assert_rollback()

    def test_perfil_eliminado_no_transiciona(self):
        PerfilUsuario.objects.filter(usuario=self.user).update(deleted=True)
        self.assertEqual(self.finish().status_code, 400)
        self.assert_rollback()

    def test_menor_carga_y_empate_determinista(self):
        busy = self.person('a-busy', 'PSICOLOGO')
        selected = self.person('b-free', 'PSICOLOGO')
        self.person('c-free', 'PSICOLOGO')
        AsignacionProfesional.objects.create(trabajador=self.person('other', 'TRABAJADOR'), psicologo=busy)
        response = self.finish()
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['estado_asignacion_profesional'], 'ASIGNADO')
        self.assertEqual(AsignacionProfesional.objects.get(trabajador=self.user).psicologo_id, selected.pk)
        self.assertEqual(self.finish().status_code, 200)
        self.assertEqual(AsignacionProfesional.objects.filter(trabajador=self.user).count(), 1)

    def test_psicologos_no_elegibles_excluidos(self):
        disabled = self.person('disabled', 'PSICOLOGO')
        PerfilUsuario.objects.filter(usuario=disabled).update(habilitado_asignaciones=False)
        self.person('inactive', 'PSICOLOGO', is_active=False)
        self.person('deleted', 'PSICOLOGO', deleted=True)
        deleted_profile = self.person('deleted-profile', 'PSICOLOGO')
        PerfilUsuario.objects.filter(usuario=deleted_profile).update(deleted=True)
        no_profile = User.objects.create_user(username='no-profile@saspel.com')
        no_profile.groups.add(Group.objects.get(name='PSICOLOGO'))
        self.person('admin', 'ADMIN')
        response = self.finish()
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['estado_asignacion_profesional'], 'PENDIENTE')
        self.assertFalse(AsignacionProfesional.objects.exists())

    def test_asignacion_preexistente_conservada(self):
        professional = self.person('existing', 'PSICOLOGO')
        assignment = AsignacionProfesional.objects.create(trabajador=self.user, psicologo=professional)
        before = list(AsignacionProfesional.objects.values())
        self.assertEqual(self.finish().status_code, 200)
        self.assertEqual(before, list(AsignacionProfesional.objects.values()))
        self.assertEqual(AsignacionProfesional.objects.get().pk, assignment.pk)

    def test_seguridad_finalizacion_y_resultado_propio(self):
        other = self.person('stranger')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(other)))
        self.assertEqual(self.finish().status_code, 404)
        other.groups.set([Group.objects.get(name='ADMIN')])
        self.assertEqual(self.finish().status_code, 403)
        self.assertEqual(self.client.get(RESULT_URL).status_code, 403)
        self.client.credentials()
        self.assertEqual(self.finish().status_code, 401)
        self.assertEqual(self.client.get(RESULT_URL).status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(self.user)))
        for field in ('user_id', 'trabajador_id', 'puntaje_total'):
            response = self.client.post(self.url, {'respuestas': self.answers(), field: str(other.pk)}, format='json')
            self.assertEqual(response.status_code, 400)
        self.assertEqual(self.finish().status_code, 200)
        other.groups.set([Group.objects.get(name='TRABAJADOR')])
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(other)))
        self.assertEqual(self.finish().status_code, 404)
        self.assertEqual(self.client.get(RESULT_URL).status_code, 404)
        self.assertEqual(self.client.get(RESULT_URL, {'user_id': str(self.user.pk)}).status_code, 404)


class CierreConcurrencyTests(CierreFixture, TransactionTestCase):
    def setUp(self):
        self.prepare()

    def test_doble_finalizacion_concurrente(self):
        self.person('psychologist', 'PSICOLOGO')
        answers = tuple(RespuestaEvaluacion(UUID(a['pregunta_id']), UUID(a['opcion_id'])) for a in self.answers())
        barrier = Barrier(2)

        def finish(_):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return build_responder_evaluacion().finalizar(self.user.pk, self.assignment.pk, answers)
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(finish, index) for index in range(2)]
            results = [future.result(timeout=20) for future in futures]
        self.assertEqual(results[0], results[1])
        self.assertEqual(ResultadoInstrumento.objects.count(), 1)
        self.assertEqual(AsignacionProfesional.objects.count(), 1)
        self.assertEqual(RespuestaPregunta.objects.count(), 10)
