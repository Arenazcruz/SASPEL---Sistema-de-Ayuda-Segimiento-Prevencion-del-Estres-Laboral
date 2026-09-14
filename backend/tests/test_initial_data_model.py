"""Este archivo comprueba áreas, cargos, perfiles, roles y asignaciones de psicólogos.

Por ejemplo, verifica que dos empleados no compartan código, que un trabajador
no tenga dos psicólogos asignados a la vez y que se conserve su historial.
También comprueba que preparar los grupos varias veces no los duplique ni haga
perder sus miembros. Todos los ejemplos se ejecutan en una base temporal.
"""

from importlib import import_module

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from src.infrastructure.persistence.django.models import (
    AreaInstitucional,
    AsignacionProfesional,
    CargoInstitucional,
    PerfilUsuario,
)


class InitialDataModelTests(TestCase):
    """Comprueba los datos institucionales y el historial de asignaciones."""
    @classmethod
    def setUpTestData(cls):
        """Crea cuentas ficticias compartidas para probar perfiles y vínculos en la BD temporal."""
        User = get_user_model()
        cls.trabajador = User.objects.create_user(username='trabajador')
        cls.psicologo = User.objects.create_user(username='psicologo')
        cls.otro_psicologo = User.objects.create_user(username='otro_psicologo')

    def test_crear_area(self):
        area = AreaInstitucional.objects.create(nombre='Administración')
        area.refresh_from_db()
        self.assertTrue(area.activo)
        self.assertEqual(area.descripcion, '')
        self.assertEqual(str(area), 'Administración')
        self.assertIsNotNone(area.creado_en)
        self.assertIsNotNone(area.actualizado_en)

    def test_crear_cargo(self):
        cargo = CargoInstitucional.objects.create(nombre='Analista')
        cargo.refresh_from_db()
        self.assertTrue(cargo.activo)
        self.assertEqual(cargo.descripcion, '')
        self.assertEqual(str(cargo), 'Analista')
        self.assertIsNotNone(cargo.creado_en)
        self.assertIsNotNone(cargo.actualizado_en)

    def test_nombres_institucionales_unicos_y_obligatorios(self):
        for model in (AreaInstitucional, CargoInstitucional):
            with self.subTest(model=model.__name__):
                with self.assertRaises(ValidationError):
                    model(nombre='').full_clean()
                model.objects.create(nombre='Nombre único')
                with self.assertRaises(IntegrityError), transaction.atomic():
                    model.objects.create(nombre='Nombre único')

    def test_crear_perfil_con_datos_opcionales_vacios(self):
        perfil = PerfilUsuario.objects.create(
            usuario=self.trabajador, codigo_empleado='EMP-001',
        )
        perfil.refresh_from_db()
        perfil.full_clean()
        self.assertEqual(self.trabajador.perfil_usuario, perfil)
        self.assertFalse(perfil.tamizaje_resuelto)
        self.assertTrue(perfil.habilitado_asignaciones)
        self.assertIsNone(perfil.area)
        self.assertIsNone(perfil.cargo)
        self.assertIsNone(perfil.fecha_nacimiento)
        self.assertEqual(str(perfil), 'EMP-001')

    def test_codigo_empleado_no_puede_duplicarse(self):
        PerfilUsuario.objects.create(usuario=self.trabajador, codigo_empleado='EMP-001')
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilUsuario.objects.create(usuario=self.psicologo, codigo_empleado='EMP-001')

    def test_usuario_solo_puede_tener_un_perfil(self):
        PerfilUsuario.objects.create(usuario=self.trabajador, codigo_empleado='EMP-001')
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilUsuario.objects.create(usuario=self.trabajador, codigo_empleado='EMP-002')

    def test_area_y_cargo_referenciados_estan_protegidos(self):
        area = AreaInstitucional.objects.create(nombre='Administración')
        cargo = CargoInstitucional.objects.create(nombre='Analista')
        perfil = PerfilUsuario.objects.create(
            usuario=self.trabajador, codigo_empleado='EMP-001', area=area, cargo=cargo,
        )
        for catalogo in (area, cargo):
            with self.subTest(model=type(catalogo).__name__):
                with self.assertRaises(ProtectedError):
                    catalogo.delete()
        self.assertEqual(perfil.area, area)
        self.assertEqual(perfil.cargo, cargo)

    def test_eliminar_usuario_sin_asignaciones_elimina_su_perfil(self):
        perfil = PerfilUsuario.objects.create(usuario=self.trabajador, codigo_empleado='EMP-001')
        self.trabajador.delete()
        self.assertFalse(PerfilUsuario.objects.filter(pk=perfil.pk).exists())

    def test_habilitacion_es_independiente_de_usuario_activo(self):
        perfil = PerfilUsuario.objects.create(
            usuario=self.psicologo, codigo_empleado='PSI-001', habilitado_asignaciones=False,
        )
        perfil.refresh_from_db()
        self.assertFalse(perfil.habilitado_asignaciones)
        self.assertTrue(perfil.usuario.is_active)

    def test_crear_asignacion_profesional(self):
        asignacion = AsignacionProfesional.objects.create(
            trabajador=self.trabajador, psicologo=self.psicologo,
        )
        asignacion.refresh_from_db()
        self.assertEqual(asignacion.estado, AsignacionProfesional.Estado.ACTIVA)
        self.assertIsNotNone(asignacion.fecha_asignacion)
        self.assertIsNotNone(asignacion.creado_en)
        self.assertIsNotNone(asignacion.actualizado_en)
        self.assertIsNone(asignacion.fecha_fin)
        self.assertEqual(self.trabajador.asignaciones_como_trabajador.get(), asignacion)
        self.assertEqual(self.psicologo.asignaciones_como_psicologo.get(), asignacion)

    def test_trabajador_no_puede_tener_dos_asignaciones_activas(self):
        AsignacionProfesional.objects.create(trabajador=self.trabajador, psicologo=self.psicologo)
        with self.assertRaises(IntegrityError), transaction.atomic():
            AsignacionProfesional.objects.create(
                trabajador=self.trabajador, psicologo=self.otro_psicologo,
            )

    def test_usuario_no_puede_asignarse_a_si_mismo(self):
        for estado in AsignacionProfesional.Estado.values:
            with self.subTest(estado=estado):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    AsignacionProfesional.objects.create(
                        trabajador=self.trabajador, psicologo=self.trabajador, estado=estado,
                    )

    def test_historial_finalizado_y_reasignado_coexiste_con_asignacion_activa(self):
        """Conserva vínculos cerrados al añadir uno activo; la unicidad solo limita la asignación
        vigente.
        """
        historial = []
        for estado in ('FINALIZADA', 'REASIGNADA'):
            anterior = AsignacionProfesional.objects.create(
                trabajador=self.trabajador, psicologo=self.psicologo,
            )
            anterior.estado = estado
            anterior.fecha_fin = timezone.now()
            anterior.motivo_fin = 'Cambio de profesional'
            anterior.save()
            historial.append(anterior.pk)
        AsignacionProfesional.objects.create(
            trabajador=self.trabajador, psicologo=self.otro_psicologo,
        )
        self.assertEqual(self.trabajador.asignaciones_como_trabajador.count(), 3)
        self.assertEqual(
            AsignacionProfesional.objects.filter(pk__in=historial, fecha_fin__isnull=False).count(), 2,
        )
        anterior.estado = 'ACTIVA'
        with self.assertRaises(IntegrityError), transaction.atomic():
            anterior.save()

    def test_usuarios_con_historial_estan_protegidos(self):
        asignacion = AsignacionProfesional.objects.create(
            trabajador=self.trabajador, psicologo=self.psicologo,
            estado='FINALIZADA', fecha_fin=timezone.now(),
        )
        for usuario in (self.trabajador, self.psicologo):
            with self.subTest(usuario=usuario.username):
                with self.assertRaises(ProtectedError):
                    usuario.delete()
        self.assertTrue(AsignacionProfesional.objects.filter(pk=asignacion.pk).exists())

    def test_estado_fuera_del_catalogo_es_rechazado_por_bd(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            AsignacionProfesional.objects.create(
                trabajador=self.trabajador, psicologo=self.psicologo, estado='INVALIDA',
            )


class InitialRolesMigrationTests(TestCase):
    """Comprueba que los grupos se preparen sin duplicarse ni perder miembros."""
    ROLES = {'NUEVO_TRABAJADOR', 'TRABAJADOR', 'PSICOLOGO', 'ADMIN', 'SUPERADMIN'}

    def test_cinco_grupos_existen_despues_de_migraciones(self):
        self.assertEqual(set(Group.objects.values_list('name', flat=True)), self.ROLES)
        self.assertFalse(get_user_model().objects.exists())
        self.assertFalse(Group.permissions.through.objects.exists())

    def test_migracion_idempotente_y_reversion_conserva_membresias(self):
        migration = import_module(
            'src.infrastructure.persistence.django.migrations.0002_crear_roles_iniciales'
        )
        state = MigrationExecutor(connection).loader.project_state([
            ('api', '0002_crear_roles_iniciales'),
        ])
        # Simulamos que falta un grupo y comprobamos que se recupere sin perder los demás.
        Group.objects.filter(name='NUEVO_TRABAJADOR').delete()
        group = Group.objects.get(name='PSICOLOGO')
        usuario = get_user_model().objects.create_user(username='profesional')
        usuario.groups.add(group)
        permiso = Permission.objects.get(content_type__app_label='auth', codename='view_user')
        group.permissions.add(permiso)
        unrelated = Group.objects.create(name='GRUPO_EXISTENTE')
        with connection.schema_editor() as editor:
            migration.crear_roles(state.apps, editor)
            ids = dict(Group.objects.values_list('name', 'pk'))
            migration.crear_roles(state.apps, editor)
            migration.Migration.operations[0].reverse_code(state.apps, editor)
            migration.crear_roles(state.apps, editor)
        self.assertEqual(dict(Group.objects.values_list('name', 'pk')), ids)
        self.assertEqual(set(ids), self.ROLES | {unrelated.name})
        self.assertTrue(usuario.groups.filter(pk=group.pk).exists())
        self.assertTrue(group.permissions.filter(pk=permiso.pk).exists())
