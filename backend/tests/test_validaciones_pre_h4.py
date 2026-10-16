"""Regresiones de la auditoría preventiva; datos exclusivos de la BD temporal."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from src.application.use_cases.assignments import AutoAssignWorker
from src.infrastructure.persistence.django.repositories.assignments import DjangoAssignmentRepository
from src.infrastructure.persistence.django.models import (
    AreaInstitucional, CargoInstitucional, InstrumentoPsicologico, EscalaRespuesta,
    PreguntaInstrumento, OpcionRespuesta, RangoInterpretacion, AsignacionProfesional,
)
from tests.test_assignments_api import person


@override_settings(
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    CACHES={
        'default': {'BACKEND':'django.core.cache.backends.locmem.LocMemCache'},
        'login_attempts': {'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'audit-pre-h4'},
    },
)
class ValidacionesPreH4Tests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.root = person('audit-root', 'SUPERADMIN')
        self.auth(self.root)
        self.instrument = InstrumentoPsicologico.objects.create(codigo='AUDIT', nombre='Prueba')
        self.scale = EscalaRespuesta.objects.create(nombre='Prueba')

    def auth(self, user):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(user)))

    def test_cuenta_borrada_no_inicia_ni_renueva_ni_utiliza_sesion(self):
        user = get_user_model().objects.create_user(
            username='audit-login@saspel.com', email='audit-login@saspel.com', password='Audit-password-2026!',
        )
        user.groups.add(Group.objects.get(name='SUPERADMIN'))
        access, refresh = str(AccessToken.for_user(user)), str(RefreshToken.for_user(user))
        user.deleted = True
        user.save(update_fields=['deleted'])
        self.client.credentials()
        response = self.client.post('/api/auth/login/', {
            'email': user.email, 'password': 'Audit-password-2026!',
        }, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertNotIn('access', response.data)
        self.assertEqual(self.client.post('/api/auth/refresh/', {'refresh': refresh}, format='json').status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access)
        for path in ['/api/auth/me/', '/api/superadmin/users/']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 401)
        user.refresh_from_db()
        self.assertIsNone(user.last_login)

    def test_catalogos_borrados_no_se_listan_ni_editan_ni_reactivan(self):
        base = '/api/superadmin/'
        cases = [
            (AreaInstitucional.objects.create(nombre='Borrada'), base+'areas/', {'nombre':'Cambio'}),
            (CargoInstitucional.objects.create(nombre='Borrado'), base+'cargos/', {'nombre':'Cambio'}),
            (self.instrument, base+'instruments/', {'nombre':'Cambio'}),
            (self.scale, base+'scales/', {'nombre':'Cambio'}),
        ]
        for row, path, data in cases:
            with self.subTest(path=path):
                row.deleted = True
                row.save(update_fields=['deleted'])
                listed = self.client.get(path)
                items = listed.data['results'] if isinstance(listed.data, dict) else listed.data
                self.assertNotIn(row.pk, [item['id'] for item in items])
                detail = f'{path}{row.pk}/'
                self.assertEqual(self.client.get(detail).status_code, 404)
                self.assertEqual(self.client.patch(detail, data, format='json').status_code, 404)
                self.assertEqual(self.client.post(detail+'activate/', {}, format='json').status_code, 404)

    def test_contenido_borrado_y_padres_borrados_no_admiten_acceso(self):
        q = PreguntaInstrumento.objects.create(instrumento=self.instrument, texto='Pregunta', orden=1, tipo_respuesta='TEXTO')
        o = OpcionRespuesta.objects.create(escala=self.scale, etiqueta='Opción', valor=0, orden=1)
        r = RangoInterpretacion.objects.create(instrumento=self.instrument, nombre='Rango', orden=1, puntaje_minimo=0, puntaje_maximo=5)
        for row, path in [(q, f'instruments/{self.instrument.pk}/questions/'),
                          (r, f'instruments/{self.instrument.pk}/ranges/'),
                          (o, f'scales/{self.scale.pk}/options/')]:
            url = '/api/superadmin/'+path
            with self.subTest(path=path):
                row.deleted = True
                row.save(update_fields=['deleted'])
                self.assertEqual(self.client.get(url).data['count'], 0)
                self.assertEqual(self.client.get(f'{url}{row.pk}/').status_code, 404)
                self.assertEqual(self.client.post(f'{url}{row.pk}/activate/', {}, format='json').status_code, 404)
                row.deleted = False
                row.save(update_fields=['deleted'])
        self.instrument.deleted = True
        self.instrument.save(update_fields=['deleted'])
        url = f'/api/superadmin/instruments/{self.instrument.pk}/questions/'
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get(f'{url}{q.pk}/').status_code, 404)
        self.assertEqual(self.client.post(url, {'texto':'Otra', 'orden':2, 'tipo_respuesta':'TEXTO'}, format='json').status_code, 404)
        self.scale.deleted = True
        self.scale.save(update_fields=['deleted'])
        other = InstrumentoPsicologico.objects.create(codigo='OTRO', nombre='Otro')
        self.assertEqual(self.client.post(f'/api/superadmin/instruments/{other.pk}/questions/', {
            'texto':'Ajena', 'orden':1, 'tipo_respuesta':'ESCALA', 'escala_id':str(self.scale.pk),
        }, format='json').status_code, 404)

    def test_usuario_borrado_no_se_edita_ni_aparece_como_destinatario(self):
        worker = person('audit-deleted', 'TRABAJADOR')
        worker.deleted = True
        worker.save(update_fields=['deleted'])
        url = f'/api/superadmin/users/{worker.pk}/'
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.patch(url, {'first_name':'Cambio'}, format='json').status_code, 404)
        self.assertEqual(self.client.post(url+'activate/', {}, format='json').status_code, 404)
        self.assertNotIn(worker.pk, [r['id'] for r in self.client.get('/api/superadmin/users/').data['results']])
        self.assertNotIn(worker.pk, [r['id'] for r in self.client.get('/api/superadmin/assignments/unassigned-workers/').data['results']])
        worker.refresh_from_db()
        self.assertEqual(worker.first_name, 'audit-deleted')

    def test_asignacion_no_admite_persona_o_perfil_borrado(self):
        worker = person('audit-worker', 'TRABAJADOR')
        psy = person('audit-psy', 'PSICOLOGO')
        for row in [worker, psy.perfil_usuario]:
            with self.subTest(model=type(row).__name__):
                row.deleted = True
                row.save(update_fields=['deleted'])
                response = self.client.post('/api/superadmin/assignments/', {
                    'trabajador_id':str(worker.pk), 'psicologo_id':str(psy.pk),
                }, format='json')
                self.assertIn(response.status_code, (400,404))
                self.assertFalse(AsignacionProfesional.objects.exists())
                row.deleted = False
                row.save(update_fields=['deleted'])

    def test_empate_de_carga_respeta_antiguedad_ultima_asignacion(self):
        worker = person('audit-target', 'TRABAJADOR')
        past_worker = person('audit-past', 'TRABAJADOR')
        recent = person('a-recent', 'PSICOLOGO')
        oldest = person('z-oldest', 'PSICOLOGO')
        for psy, days in [(recent,1),(oldest,10)]:
            row = AsignacionProfesional.objects.create(trabajador=past_worker, psicologo=psy, estado='FINALIZADA', fecha_fin=timezone.now(), motivo_fin='Histórico')
            AsignacionProfesional.objects.filter(pk=row.pk).update(fecha_asignacion=timezone.now()-timedelta(days=days))
        AutoAssignWorker(DjangoAssignmentRepository()).execute(worker.pk)
        self.assertEqual(AsignacionProfesional.objects.get(trabajador=worker, estado='ACTIVA').psicologo_id, oldest.pk)

    def test_paginacion_extrema_no_produce_error_de_servidor(self):
        for path, key in [('/api/superadmin/users/','page'), ('/api/superadmin/instruments/','page'),
                          ('/api/superadmin/scales/','page'), ('/api/superadmin/assignments/','page'),
                          ('/api/superadmin/assignments/unassigned-workers/','page'), ('/api/reportes/usuarios/','pagina')]:
            with self.subTest(path=path):
                response = self.client.get(path, {key: str(10**30)})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data.get('results', response.data.get('filas')), [])

    def test_administrador_sin_perfil_conserva_acceso_operativo_no_clinico(self):
        root = person('audit-bootstrap', 'SUPERADMIN', profile=False)
        self.auth(root)
        for path in ['/api/dashboard/', '/api/reportes/usuarios/', '/api/alertas/reglas/', '/api/notificaciones/']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
        self.assertEqual(self.client.get('/api/alertas/').status_code, 403)
        self.assertEqual(self.client.get('/api/trabajador/resultados/').status_code, 403)

    def test_asignacion_borrada_no_admite_transiciones(self):
        worker = person('audit-assigned', 'TRABAJADOR')
        psy = person('audit-assigned-psy', 'PSICOLOGO')
        row = AsignacionProfesional.objects.create(trabajador=worker, psicologo=psy, deleted=True)
        response = self.client.post(f'/api/superadmin/assignments/{row.pk}/finish/', {'motivo_fin':'Cierre'}, format='json')
        self.assertEqual(response.status_code, 404)
        row.refresh_from_db()
        self.assertEqual(row.estado, 'ACTIVA')

    def test_administrador_borrado_no_cuenta_para_proteger_el_ultimo_acceso(self):
        removed = person('audit-removed-admin', 'SUPERADMIN')
        get_user_model().objects.filter(pk=removed.pk).update(deleted=True)
        from src.infrastructure.persistence.django.repositories.administration import DjangoAdministrationRepository
        self.assertEqual(DjangoAdministrationRepository().active_superadmins(), 1)

    def test_duplicado_de_contenido_no_revela_nombre_de_constraint(self):
        PreguntaInstrumento.objects.create(instrumento=self.instrument, texto='Original', orden=1, tipo_respuesta='TEXTO')
        response = self.client.post(f'/api/superadmin/instruments/{self.instrument.pk}/questions/', {
            'texto':'Duplicada', 'orden':1, 'tipo_respuesta':'TEXTO',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('saspel_', str(response.data))
        self.assertNotIn('__all__', response.data)
        self.assertEqual(PreguntaInstrumento.objects.count(), 1)

    def test_reordenar_conserva_ordenes_reservados_por_borrados(self):
        hidden = PreguntaInstrumento.objects.create(instrumento=self.instrument, texto='Histórica', orden=0, tipo_respuesta='TEXTO', deleted=True)
        first = PreguntaInstrumento.objects.create(instrumento=self.instrument, texto='Primera', orden=1, tipo_respuesta='TEXTO')
        second = PreguntaInstrumento.objects.create(instrumento=self.instrument, texto='Segunda', orden=2, tipo_respuesta='TEXTO')
        response = self.client.post(f'/api/superadmin/instruments/{self.instrument.pk}/questions/{second.pk}/move/', {'direction':'up'}, format='json')
        self.assertEqual(response.status_code, 200)
        hidden.refresh_from_db();first.refresh_from_db();second.refresh_from_db()
        self.assertEqual((hidden.orden, first.orden, second.orden), (0,2,1))
