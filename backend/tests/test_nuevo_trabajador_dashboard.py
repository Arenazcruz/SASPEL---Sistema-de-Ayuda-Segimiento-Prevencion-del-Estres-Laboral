from datetime import timedelta
from uuid import UUID

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from src.infrastructure.persistence.django.models import (
    AceptacionPolitica, AsignacionInstrumento, InstrumentoPsicologico,
    PerfilUsuario, PoliticaSistema,
)

User = get_user_model()
URL = '/api/nuevo-trabajador/dashboard/'


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class NuevoTrabajadorDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='ana@saspel.com', email='ana@saspel.com', first_name='Ana', last_name='Prueba',
        )
        self.user.groups.add(Group.objects.get(name='NUEVO_TRABAJADOR'))
        PerfilUsuario.objects.create(usuario=self.user, codigo_empleado='DASH-1')
        self.other = User.objects.create_user(username='otra@saspel.com')
        self.instrumento = InstrumentoPsicologico.objects.create(
            codigo='INICIAL-TEST', nombre='Instrumento inicial de prueba', version='2.1', es_inicial=True,
        )
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(self.user)))

    def asignar(self, **changes):
        return AsignacionInstrumento.objects.create(**(dict(
            trabajador=self.user, instrumento=self.instrumento, origen='SISTEMA',
        ) | changes))

    def evaluacion(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertEqual(set(response.json()), {'evaluacion_inicial'})
        return response.json()['evaluacion_inicial']

    def test_sin_asignar(self):
        self.assertEqual(self.evaluacion(), dict(
            estado='SIN_ASIGNAR', asignacion_id=None, instrumento_id=None, nombre=None,
            version=None, fecha_asignacion=None, fecha_limite=None, puede_iniciar=False,
        ))
        self.assertFalse(AsignacionInstrumento.objects.exists())

    def test_estados_reales_uuid_y_contrato_minimo(self):
        asignacion = self.asignar(fecha_limite=timezone.now() + timedelta(days=5))
        for estado in ('PENDIENTE', 'EN_PROGRESO', 'COMPLETADA'):
            with self.subTest(estado=estado):
                AsignacionInstrumento.objects.filter(pk=asignacion.pk).update(estado=estado)
                data = self.evaluacion()
                self.assertEqual(set(data), {
                    'estado', 'asignacion_id', 'instrumento_id', 'nombre', 'version',
                    'fecha_asignacion', 'fecha_limite', 'puede_iniciar',
                })
                self.assertEqual(data['estado'], estado)
                self.assertEqual(UUID(data['asignacion_id']), asignacion.pk)
                self.assertEqual(UUID(data['instrumento_id']), self.instrumento.pk)
                self.assertEqual(data['nombre'], self.instrumento.nombre)
                self.assertEqual(data['version'], '2.1')
                self.assertIsNotNone(data['fecha_asignacion'])
                self.assertIsNotNone(data['fecha_limite'])

    def test_fecha_limite_opcional(self):
        self.asignar()
        self.assertIsNone(self.evaluacion()['fecha_limite'])

    def test_solo_considera_instrumentos_iniciales(self):
        self.instrumento.es_inicial = False
        self.instrumento.save()
        self.asignar()
        self.assertEqual(self.evaluacion()['estado'], 'SIN_ASIGNAR')

    def test_no_expone_asignaciones_ajenas_ni_acepta_usuario_por_query(self):
        self.asignar(trabajador=self.other)
        response = self.client.get(URL, {'user_id': str(self.other.pk)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['evaluacion_inicial']['estado'], 'SIN_ASIGNAR')

    def test_elige_la_asignacion_mas_reciente_no_cancelada(self):
        anterior = self.asignar(estado='COMPLETADA')
        AsignacionInstrumento.objects.filter(pk=anterior.pk).update(fecha_asignacion=timezone.now() - timedelta(days=1))
        actual = self.asignar()
        self.asignar(estado='CANCELADA')
        self.assertEqual(self.evaluacion()['asignacion_id'], str(actual.pk))

    def test_canceladas_y_borrados_logicos_no_aparecen(self):
        self.asignar(estado='CANCELADA')
        self.asignar(deleted=True)
        self.assertEqual(self.evaluacion()['estado'], 'SIN_ASIGNAR')
        self.asignar()
        self.instrumento.deleted = True
        self.instrumento.save()
        self.assertEqual(self.evaluacion()['estado'], 'SIN_ASIGNAR')

    def test_conserva_historial_de_version_inactiva(self):
        self.asignar(estado='COMPLETADA')
        self.instrumento.activo = False
        self.instrumento.save()
        self.assertEqual(self.evaluacion()['estado'], 'COMPLETADA')

    def test_otros_roles_y_usuario_sin_rol_reciben_403(self):
        for role in ('TRABAJADOR', 'PSICOLOGO', 'ADMIN', 'SUPERADMIN', None):
            with self.subTest(role=role):
                self.user.groups.clear()
                if role:
                    self.user.groups.add(Group.objects.get(name=role))
                self.assertEqual(self.client.get(URL).status_code, 403)

    def test_prioridad_de_roles_impide_acceso_con_grupo_adicional(self):
        self.user.groups.add(Group.objects.get(name='ADMIN'))
        self.assertEqual(self.client.get(URL).status_code, 403)

    def test_sin_jwt_y_jwt_invalido_reciben_401(self):
        self.client.credentials()
        self.assertEqual(self.client.get(URL).status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid')
        self.assertEqual(self.client.get(URL).status_code, 401)

    def test_exige_password_y_politicas_antes_del_dashboard(self):
        self.user.debe_cambiar_password = True
        self.user.save()
        self.assertEqual(self.client.get(URL).status_code, 403)
        self.user.debe_cambiar_password = False
        self.user.save()
        politica = PoliticaSistema.objects.create(
            tipo='PRIVACIDAD_DATOS', titulo='Política de prueba', version='1', contenido='Prueba',
            vigente_desde=timezone.now() - timedelta(days=1), obligatoria=True, activo=True,
        )
        self.assertEqual(self.client.get(URL).status_code, 403)
        AceptacionPolitica.objects.create(usuario=self.user, politica=politica)
        self.assertEqual(self.client.get(URL).status_code, 200)

    def test_consulta_no_modifica_usuario_perfil_asignaciones_ni_auditoria(self):
        self.asignar(estado='COMPLETADA')
        models = (User, PerfilUsuario, AsignacionInstrumento, InstrumentoPsicologico)
        before = [list(model.objects.order_by('pk').values()) for model in models]
        self.evaluacion()
        self.assertEqual(before, [list(model.objects.order_by('pk').values()) for model in models])
        self.assertEqual(list(self.user.groups.values_list('name', flat=True)), ['NUEVO_TRABAJADOR'])

    def test_endpoint_no_admite_mutaciones(self):
        for method in ('post', 'put', 'patch', 'delete'):
            with self.subTest(method=method):
                self.assertEqual(getattr(self.client, method)(URL, {}, format='json').status_code, 405)
