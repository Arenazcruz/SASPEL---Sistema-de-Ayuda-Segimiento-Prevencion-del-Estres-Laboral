from contextlib import nullcontext
from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from src.application.use_cases.resultados import ConsultarResultados
from src.domain.exceptions.resultados import AccesoResultadosDenegado, ResultadoNoDisponible
from src.infrastructure.persistence.django.models import (
    AplicacionInstrumento, AreaInstitucional, AsignacionInstrumento, AsignacionProfesional,
    CargoInstitucional, InstrumentoPsicologico, PerfilUsuario, RangoInterpretacion, ResultadoInstrumento,
)

User = get_user_model()
OWN = '/api/trabajador/resultados/'
WORKERS = '/api/psicologo/trabajadores/'
PRO_RESULTS = '/api/psicologo/resultados/'


class AutorizacionResultadosTests(SimpleTestCase):
    def test_autorizacion_profesional_se_aplica_sin_http(self):
        repository = Mock()
        repository.atomic.side_effect = nullcontext
        repository.rol_activo.return_value = 'PSICOLOGO'
        repository.tiene_asignacion_activa.return_value = False
        case = ConsultarResultados(repository)
        psychologist, worker, result_id = uuid4(), uuid4(), uuid4()
        repository.resultado.return_value = (worker, Mock())
        for call in (lambda: case.de_trabajador(psychologist, worker),
                     lambda: case.detalle_profesional(psychologist, result_id)):
            with self.assertRaises(ResultadoNoDisponible):
                call()
        repository.listar_resultados.assert_not_called()
        repository.tiene_asignacion_activa.return_value = True
        case.de_trabajador(psychologist, worker)
        repository.listar_resultados.assert_called_once_with(worker)
        repository.rol_activo.return_value = 'ADMIN'
        with self.assertRaises(AccesoResultadosDenegado):
            case.de_trabajador(psychologist, worker)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ResultadosHistorialTests(TestCase):
    def person(self, name, role):
        user = User.objects.create_user(username=f'{name}@saspel.com', email=f'{name}@saspel.com', first_name=name)
        user.groups.add(Group.objects.get(name=role))
        PerfilUsuario.objects.create(usuario=user, codigo_empleado=name, apellido_materno='Materno')
        return user

    def result(self, worker, instrument=None, days=0, score='19.0000', state='FINALIZADA', rango=None):
        assignment = AsignacionInstrumento.objects.create(
            trabajador=worker, instrumento=instrument or self.instrument, origen='SISTEMA', estado='COMPLETADA',
        )
        date = timezone.now() + timedelta(days=days)
        app = AplicacionInstrumento.objects.create(asignacion=assignment, estado=state, fecha_inicio=date,
                                                   fecha_finalizacion=date if state == 'FINALIZADA' else None)
        return ResultadoInstrumento.objects.create(aplicacion=app, puntaje_total=Decimal(score), rango=rango, fecha_calculo=date)

    def authorize(self, user):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(user)))

    def setUp(self):
        self.worker = self.person('Ana', 'TRABAJADOR')
        self.other = self.person('Beatriz', 'TRABAJADOR')
        self.empty = self.person('Carmen', 'TRABAJADOR')
        self.psychologist = self.person('Psicologo', 'PSICOLOGO')
        self.other_psychologist = self.person('OtroPsicologo', 'PSICOLOGO')
        self.link = AsignacionProfesional.objects.create(trabajador=self.worker, psicologo=self.psychologist)
        AsignacionProfesional.objects.create(trabajador=self.empty, psicologo=self.psychologist)
        AsignacionProfesional.objects.create(trabajador=self.other, psicologo=self.other_psychologist)
        self.instrument = InstrumentoPsicologico.objects.create(codigo='HIST', nombre='Instrumento original', version='1.0')
        self.range = RangoInterpretacion.objects.create(instrumento=self.instrument, nombre='Configurado', orden=1,
                                                       puntaje_minimo=0, puntaje_maximo=40, interpretacion='Interpretación original')
        self.first = self.result(self.worker, days=-10, rango=self.range)
        later = InstrumentoPsicologico.objects.create(codigo='NEXT', nombre='Otro instrumento', version='2.0')
        self.last = self.result(self.worker, later, days=-1, score='7.0000')
        self.foreign = self.result(self.other)
        self.client = APIClient()
        self.authorize(self.worker)

    def test_historial_propio_multiple_ordenado_y_sin_campos_sensibles(self):
        response = self.client.get(OWN, {'trabajador_id': str(self.other.pk)})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([r['id'] for r in data], [str(self.last.pk), str(self.first.pk)])
        self.assertEqual(data[0]['instrumento'], 'Otro instrumento')
        self.assertEqual(data[0]['version'], '2.0')
        self.assertEqual(data[0]['puntaje'], '7.0000')
        self.assertIsNone(data[0]['rango'])
        self.assertEqual(data[0]['interpretacion'], '')
        self.assertEqual(set(data[0]), {'id', 'instrumento', 'version', 'fecha', 'puntaje', 'rango', 'interpretacion', 'estado'})
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_detalle_propio_conserva_version_y_relaciones_historicas(self):
        self.instrument.activo = False
        self.instrument.save()
        self.range.activo = False
        self.range.save()
        with patch('src.application.use_cases.responder_evaluacion.calcular_puntaje', side_effect=AssertionError('No recalcular')):
            response = self.client.get(f'{OWN}{self.first.pk}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['instrumento'], 'Instrumento original')
        self.assertEqual(data['version'], '1.0')
        self.assertEqual(data['rango'], 'Configurado')
        self.assertEqual(data['interpretacion'], 'Interpretación original')
        self.assertEqual(data['estado'], 'FINALIZADA')
        self.assertEqual(ResultadoInstrumento.objects.get(pk=data['id']).aplicacion_id, self.first.aplicacion_id)
        self.assertEqual(self.first.aplicacion.asignacion.instrumento_id, self.instrument.pk)

    def test_no_accede_a_detalle_ajeno_ni_inexistente(self):
        for result_id in (self.foreign.pk, uuid4()):
            response = self.client.get(f'{OWN}{result_id}/')
            self.assertEqual(response.status_code, 404)
            self.assertNotIn('puntaje', response.json())

    def test_trabajador_sin_resultados(self):
        self.authorize(self.empty)
        self.assertEqual(self.client.get(OWN).json(), [])

    def test_solo_resultados_finalizados_y_no_eliminados(self):
        hidden = self.result(self.worker, state='INICIADA')
        self.assertEqual(len(self.client.get(OWN).json()), 2)
        self.assertEqual(self.client.get(f'{OWN}{hidden.pk}/').status_code, 404)
        for model, pk in ((ResultadoInstrumento, self.first.pk), (AplicacionInstrumento, self.first.aplicacion_id),
                          (AsignacionInstrumento, self.first.aplicacion.asignacion_id)):
            with self.subTest(model=model):
                model.objects.filter(pk=pk).update(deleted=True)
                self.assertEqual([r['id'] for r in self.client.get(OWN).json()], [str(self.last.pk)])
                self.assertEqual(self.client.get(f'{OWN}{self.first.pk}/').status_code, 404)
                model.objects.filter(pk=pk).update(deleted=False)

    def test_psicologo_lista_solo_asignados_y_datos_minimos(self):
        area = AreaInstitucional.objects.create(nombre='Operaciones')
        cargo = CargoInstitucional.objects.create(nombre='Analista')
        PerfilUsuario.objects.filter(usuario=self.worker).update(area=area, cargo=cargo)
        self.authorize(self.psychologist)
        response = self.client.get(WORKERS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['cantidad'], 2)
        self.assertEqual([w['id'] for w in data['trabajadores']], [str(self.worker.pk), str(self.empty.pk)])
        first = data['trabajadores'][0]
        self.assertEqual(first['nombre_completo'], 'Ana Materno')
        self.assertEqual(first['area'], 'Operaciones')
        self.assertEqual(first['cargo'], 'Analista')
        self.assertEqual(first['estado'], 'ACTIVA')
        self.assertEqual(set(first), {'id', 'nombre_completo', 'email', 'area', 'cargo', 'fecha_asignacion', 'estado'})

    def test_psicologo_consulta_historial_y_detalle_autorizado(self):
        self.authorize(self.psychologist)
        response = self.client.get(f'{WORKERS}{self.worker.pk}/resultados/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r['id'] for r in response.json()], [str(self.last.pk), str(self.first.pk)])
        self.assertEqual(self.client.get(f'{PRO_RESULTS}{self.first.pk}/').json(), response.json()[1])
        self.assertEqual(self.client.get(f'{WORKERS}{self.empty.pk}/resultados/').json(), [])

    def test_psicologo_ajeno_e_historial_cerrado_denegados_en_ambas_rutas(self):
        self.authorize(self.psychologist)
        self.assertEqual(self.client.get(f'{WORKERS}{self.other.pk}/resultados/').status_code, 404)
        self.assertEqual(self.client.get(f'{PRO_RESULTS}{self.foreign.pk}/').status_code, 404)
        for state in ('REASIGNADA', 'FINALIZADA'):
            AsignacionProfesional.objects.filter(pk=self.link.pk).update(estado=state)
            self.assertEqual(self.client.get(f'{WORKERS}{self.worker.pk}/resultados/').status_code, 404)
            self.assertEqual(self.client.get(f'{PRO_RESULTS}{self.first.pk}/').status_code, 404)
            self.assertEqual(self.client.get(WORKERS).json()['cantidad'], 1)

    def test_reasignacion_revoca_acceso_previo_y_autoriza_nuevo_profesional(self):
        self.authorize(self.psychologist)
        self.assertEqual(self.client.get(f'{PRO_RESULTS}{self.first.pk}/').status_code, 200)
        AsignacionProfesional.objects.filter(pk=self.link.pk).update(estado='REASIGNADA')
        AsignacionProfesional.objects.create(trabajador=self.worker, psicologo=self.other_psychologist)
        self.assertEqual(self.client.get(f'{PRO_RESULTS}{self.first.pk}/').status_code, 404)
        self.authorize(self.other_psychologist)
        self.assertEqual(self.client.get(f'{PRO_RESULTS}{self.first.pk}/').status_code, 200)

    def test_psicologo_sin_asignaciones_y_deshabilitado_para_nuevas_asignaciones(self):
        person = self.person('SinAsignaciones', 'PSICOLOGO')
        self.authorize(person)
        self.assertEqual(self.client.get(WORKERS).json(), {'cantidad': 0, 'trabajadores': []})
        # Dejar de recibir nuevas asignaciones no revoca los vínculos ACTIVA existentes.
        PerfilUsuario.objects.filter(usuario=self.psychologist).update(habilitado_asignaciones=False)
        self.authorize(self.psychologist)
        self.assertEqual(self.client.get(f'{PRO_RESULTS}{self.first.pk}/').status_code, 200)

    def test_inactivos_y_eliminados_no_filtran_informacion(self):
        self.authorize(self.psychologist)
        for model, pk, field in ((User, self.worker.pk, 'is_active'), (User, self.worker.pk, 'deleted'),
                                 (PerfilUsuario, self.worker.perfil_usuario.pk, 'deleted'),
                                 (AsignacionProfesional, self.link.pk, 'deleted')):
            with self.subTest(model=model, field=field):
                model.objects.filter(pk=pk).update(**{field: field != 'is_active'})
                self.assertEqual(self.client.get(WORKERS).json()['cantidad'], 1)
                self.assertEqual(self.client.get(f'{WORKERS}{self.worker.pk}/resultados/').status_code, 404)
                self.assertEqual(self.client.get(f'{PRO_RESULTS}{self.first.pk}/').status_code, 404)
                model.objects.filter(pk=pk).update(**{field: field == 'is_active'})
        for actor in (self.worker, self.psychologist):
            self.authorize(actor)
            url = OWN if actor == self.worker else WORKERS
            User.objects.filter(pk=actor.pk).update(is_active=False)
            self.assertEqual(self.client.get(url).status_code, 401)
            User.objects.filter(pk=actor.pk).update(is_active=True, deleted=True)
            self.assertEqual(self.client.get(url).status_code, 403)
            User.objects.filter(pk=actor.pk).update(deleted=False)

    def test_jwt_roles_primer_acceso_y_solo_lectura(self):
        endpoints = [OWN, f'{OWN}{self.first.pk}/', WORKERS,
                     f'{WORKERS}{self.worker.pk}/resultados/', f'{PRO_RESULTS}{self.first.pk}/']
        self.client.credentials()
        for url in endpoints:
            self.assertEqual(self.client.get(url).status_code, 401)
        for role in ('ADMIN', 'SUPERADMIN', 'NUEVO_TRABAJADOR'):
            actor = self.person(role, role)
            self.authorize(actor)
            for url in endpoints:
                self.assertEqual(self.client.get(url).status_code, 403)
        self.authorize(self.worker)
        for url in endpoints[2:]:
            self.assertEqual(self.client.get(url).status_code, 403)
        self.authorize(self.psychologist)
        for url in endpoints[:2]:
            self.assertEqual(self.client.get(url).status_code, 403)
        self.psychologist.debe_cambiar_password = True
        self.psychologist.save()
        self.assertEqual(self.client.get(WORKERS).status_code, 403)
        self.authorize(self.worker)
        self.assertEqual(self.client.post(OWN, {}, format='json').status_code, 405)

    def test_consultas_no_modifican_resultados_auditoria_ni_historial(self):
        models = (ResultadoInstrumento, AplicacionInstrumento, AsignacionInstrumento, AsignacionProfesional, RangoInterpretacion)
        before = [list(model.objects.order_by('pk').values()) for model in models]
        self.client.get(OWN)
        self.client.get(f'{OWN}{self.first.pk}/')
        self.authorize(self.psychologist)
        self.client.get(WORKERS)
        self.client.get(f'{WORKERS}{self.worker.pk}/resultados/')
        self.client.get(f'{PRO_RESULTS}{self.first.pk}/')
        self.assertEqual(before, [list(model.objects.order_by('pk').values()) for model in models])
