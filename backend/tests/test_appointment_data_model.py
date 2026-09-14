"""Este archivo comprueba los horarios de atención y las citas con datos de prueba.

Verifica que una cita termine después de comenzar, que los participantes sean
distintos y que las reprogramaciones conserven las citas anteriores. También
comprueba días, horarios y protección de usuarios con citas guardadas.
Los ejemplos usan una base temporal. La revisión de permisos y choques de
horarios se implementará más adelante.
"""

from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from src.infrastructure.persistence.django.models import Cita, DisponibilidadPsicologo


class DisponibilidadPsicologoTests(TestCase):
    """Comprueba los horarios habituales que puede registrar un psicólogo."""

    @classmethod
    def setUpTestData(cls):
        """Crea dos cuentas ficticias para distinguir unicidad por profesional de coincidencias
        válidas entre profesionales.
        """
        User = get_user_model()
        cls.psicologo = User.objects.create_user(username='psicologo_disponibilidad_prueba')
        cls.otro_psicologo = User.objects.create_user(username='otro_psicologo_disponibilidad_prueba')

    def crear_bloque(self, **cambios):
        """Prepara un horario de ejemplo para usarlo en las pruebas."""
        campos = {
            'psicologo': self.psicologo, 'dia_semana': 0,
            'hora_inicio': time(8), 'hora_fin': time(12),
        }
        campos.update(cambios)
        return DisponibilidadPsicologo.objects.create(**campos)

    def test_crear_disponibilidad(self):
        bloque = self.crear_bloque()
        bloque.refresh_from_db()
        bloque.full_clean()
        self.assertTrue(bloque.activo)
        self.assertEqual(bloque.get_dia_semana_display(), 'Lunes')
        self.assertEqual(self.psicologo.disponibilidades_semanales.get(), bloque)
        self.assertIsNotNone(bloque.creado_en)
        self.assertIsNotNone(bloque.actualizado_en)

    def test_rechaza_intervalos_iguales_o_invertidos(self):
        for fin in (time(8), time(7)):
            with self.subTest(fin=fin), self.assertRaises(IntegrityError), transaction.atomic():
                self.crear_bloque(hora_fin=fin)

    def test_rechaza_dias_fuera_de_cero_a_seis(self):
        for dia in (-1, 7):
            with self.subTest(dia=dia), self.assertRaises(IntegrityError), transaction.atomic():
                self.crear_bloque(dia_semana=dia)

    def test_permite_los_siete_dias(self):
        for dia in range(7):
            with self.subTest(dia=dia):
                bloque = self.crear_bloque(dia_semana=dia)
                bloque.full_clean()
        self.assertEqual(self.psicologo.disponibilidades_semanales.count(), 7)

    def test_impide_bloque_duplicado_incluso_inactivo(self):
        self.crear_bloque()
        for activo in (True, False):
            with self.subTest(activo=activo), self.assertRaises(IntegrityError), transaction.atomic():
                self.crear_bloque(activo=activo)

    def test_permite_horarios_distintos_para_mismo_psicologo(self):
        self.crear_bloque()
        otro = self.crear_bloque(hora_inicio=time(14), hora_fin=time(18))
        self.assertEqual(otro.psicologo, self.psicologo)
        self.assertEqual(self.psicologo.disponibilidades_semanales.count(), 2)

    def test_permite_mismo_horario_para_otro_psicologo(self):
        primero = self.crear_bloque()
        segundo = self.crear_bloque(psicologo=self.otro_psicologo)
        self.assertEqual(primero.hora_inicio, segundo.hora_inicio)
        self.assertNotEqual(primero.psicologo_id, segundo.psicologo_id)

    # Por ahora se guardan horarios distintos aunque coincidan en parte; su revisión vendrá
    # después.
    def test_solapamiento_de_bloques_queda_para_application(self):
        self.crear_bloque()
        segundo = self.crear_bloque(hora_inicio=time(10), hora_fin=time(14))
        self.assertTrue(DisponibilidadPsicologo.objects.filter(pk=segundo.pk).exists())

    def test_protect_impide_borrar_psicologo_con_disponibilidad(self):
        bloque = self.crear_bloque()
        with self.assertRaises(ProtectedError):
            self.psicologo.delete()
        self.assertTrue(DisponibilidadPsicologo.objects.filter(pk=bloque.pk).exists())


class CitaTests(TestCase):
    """Comprueba solicitudes de citas y conservación de reprogramaciones."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.trabajador = User.objects.create_user(username='trabajador_cita_prueba')
        cls.psicologo = User.objects.create_user(username='psicologo_cita_prueba')
        cls.solicitante = User.objects.create_user(username='solicitante_cita_prueba')
        # Usamos una fecha fija de ejemplo para que el resultado no dependa del día de
        # ejecución.
        cls.inicio = timezone.make_aware(datetime(2026, 10, 1, 10))
        cls.fin = cls.inicio + timedelta(hours=1)

    def crear_cita(self, **cambios):
        """Prepara una cita de ejemplo con trabajador, psicólogo y solicitante."""
        campos = {
            'trabajador': self.trabajador, 'psicologo': self.psicologo,
            'solicitada_por': self.solicitante,
            'fecha_inicio': self.inicio, 'fecha_fin': self.fin,
            'motivo': 'Motivo ficticio de prueba de persistencia',
        }
        campos.update(cambios)
        return Cita.objects.create(**campos)

    def test_crear_cita_valida(self):
        cita = self.crear_cita()
        cita.refresh_from_db()
        cita.full_clean()
        self.assertEqual(cita.estado, Cita.Estado.SOLICITADA)
        self.assertEqual(cita.prioridad, Cita.Prioridad.MEDIA)
        self.assertEqual(cita.motivo_cierre, '')
        self.assertIsNone(cita.cita_origen)
        self.assertEqual(cita.fecha_inicio, self.inicio)
        self.assertEqual(cita.fecha_fin, self.fin)
        self.assertIsNotNone(cita.creado_en)
        self.assertIsNotNone(cita.actualizado_en)

    def test_motivo_obligatorio_en_validacion_del_modelo(self):
        cita = self.crear_cita()
        cita.motivo = ''
        with self.assertRaises(ValidationError) as error:
            cita.full_clean()
        self.assertIn('motivo', error.exception.message_dict)

    # Comprobamos que una cita no pueda terminar antes de comenzar ni durar cero tiempo.
    def test_rechaza_fechas_iguales_o_invertidas(self):
        for fin in (self.inicio, self.inicio - timedelta(minutes=1)):
            with self.subTest(fin=fin), self.assertRaises(IntegrityError), transaction.atomic():
                self.crear_cita(fecha_fin=fin)

    def test_impide_trabajador_igual_a_psicologo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.crear_cita(psicologo=self.trabajador)

    def test_permite_todos_los_estados_solicitados(self):
        for estado in (
            'SOLICITADA', 'CONFIRMADA', 'COMPLETADA',
            'CANCELADA', 'RECHAZADA', 'REPROGRAMADA',
        ):
            with self.subTest(estado=estado):
                cita = self.crear_cita(estado=estado)
                cita.refresh_from_db()
                cita.full_clean()
                self.assertEqual(cita.estado, estado)

    def test_rechaza_estados_invalidos_en_bd(self):
        for estado in ('INVALIDO', ''):
            with self.subTest(estado=estado), self.assertRaises(IntegrityError), transaction.atomic():
                self.crear_cita(estado=estado)

    def test_permite_las_tres_prioridades(self):
        for prioridad in ('BAJA', 'MEDIA', 'ALTA'):
            with self.subTest(prioridad=prioridad):
                cita = self.crear_cita(prioridad=prioridad)
                cita.full_clean()
                self.assertEqual(cita.prioridad, prioridad)

    def test_rechaza_prioridades_invalidas_en_bd(self):
        for prioridad in ('OTRA', ''):
            with self.subTest(prioridad=prioridad), self.assertRaises(IntegrityError), transaction.atomic():
                self.crear_cita(prioridad=prioridad)

    def test_crear_reprogramacion_conserva_cita_original(self):
        original = self.crear_cita(estado='REPROGRAMADA')
        nueva = self.crear_cita(
            cita_origen=original,
            fecha_inicio=self.inicio + timedelta(days=2),
            fecha_fin=self.fin + timedelta(days=2),
        )
        original.refresh_from_db()
        self.assertEqual(original.fecha_inicio, self.inicio)
        self.assertEqual(original.fecha_fin, self.fin)
        self.assertEqual(original.estado, 'REPROGRAMADA')
        self.assertEqual(nueva.cita_origen, original)
        self.assertEqual(original.reprogramaciones.get(), nueva)
        self.assertEqual(Cita.objects.count(), 2)

    def test_cadena_de_tres_citas_preserva_antecedentes(self):
        primera = self.crear_cita(estado='REPROGRAMADA')
        segunda = self.crear_cita(
            cita_origen=primera, estado='REPROGRAMADA',
            fecha_inicio=self.inicio + timedelta(days=1), fecha_fin=self.fin + timedelta(days=1),
        )
        tercera = self.crear_cita(
            cita_origen=segunda,
            fecha_inicio=self.inicio + timedelta(days=2), fecha_fin=self.fin + timedelta(days=2),
        )
        tercera.refresh_from_db()
        self.assertEqual(tercera.cita_origen, segunda)
        self.assertEqual(tercera.cita_origen.cita_origen, primera)
        self.assertEqual(tercera.cita_origen.cita_origen.fecha_inicio, self.inicio)
        self.assertEqual(Cita.objects.count(), 3)

    # Comprobamos que una cita no pueda indicar que ella misma fue su cita anterior.
    def test_impide_autorreferencia_directa_en_bd(self):
        cita = self.crear_cita()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Cita.objects.filter(pk=cita.pk).update(cita_origen_id=cita.pk)
        cita.refresh_from_db()
        self.assertIsNone(cita.cita_origen)

    def test_protect_impide_borrar_trabajador_referenciado(self):
        cita = self.crear_cita()
        with self.assertRaises(ProtectedError):
            self.trabajador.delete()
        self.assertTrue(Cita.objects.filter(pk=cita.pk).exists())

    def test_protect_impide_borrar_psicologo_referenciado(self):
        cita = self.crear_cita()
        with self.assertRaises(ProtectedError):
            self.psicologo.delete()
        self.assertTrue(Cita.objects.filter(pk=cita.pk).exists())

    def test_protect_impide_borrar_solicitante_referenciado(self):
        cita = self.crear_cita()
        with self.assertRaises(ProtectedError):
            self.solicitante.delete()
        self.assertTrue(Cita.objects.filter(pk=cita.pk).exists())

    def test_protect_impide_borrar_antecedente_de_reprogramacion(self):
        """Vincula una cita reprogramada a su antecedente y comprueba que ese historial quede
        protegido.
        """
        original = self.crear_cita(estado='REPROGRAMADA')
        nueva = self.crear_cita(cita_origen=original)
        with self.assertRaises(ProtectedError):
            Cita.objects.filter(pk=original.pk).delete()
        nueva.refresh_from_db()
        self.assertEqual(nueva.cita_origen, original)

    def test_relaciones_diferencian_participantes_y_solicitante(self):
        cita = self.crear_cita()
        self.assertEqual(cita.trabajador, self.trabajador)
        self.assertEqual(cita.psicologo, self.psicologo)
        self.assertEqual(cita.solicitada_por, self.solicitante)
        self.assertEqual(self.trabajador.citas_como_trabajador.get(), cita)
        self.assertEqual(self.psicologo.citas_como_psicologo.get(), cita)
        self.assertEqual(self.solicitante.citas_solicitadas.get(), cita)

    def test_trabajador_o_psicologo_pueden_ser_solicitantes(self):
        for solicitante in (self.trabajador, self.psicologo):
            with self.subTest(solicitante=solicitante.pk):
                cita = self.crear_cita(solicitada_por=solicitante)
                cita.full_clean()
                self.assertEqual(cita.solicitada_por, solicitante)

    def test_solapamientos_de_citas_quedan_para_application(self):
        self.crear_cita(estado='CONFIRMADA')
        segunda = self.crear_cita(
            estado='CONFIRMADA', fecha_inicio=self.inicio + timedelta(minutes=30),
            fecha_fin=self.fin + timedelta(minutes=30),
        )
        self.assertTrue(Cita.objects.filter(pk=segunda.pk).exists())

    # Los datos de las personas se consultan desde sus cuentas y la duración se obtiene del
    # horario.
    def test_cita_no_duplica_datos_transitivos_o_derivados(self):
        prohibidos = {
            'nombre_trabajador', 'correo_trabajador', 'nombre_psicologo',
            'correo_psicologo', 'area_trabajador', 'cargo_trabajador',
            'duracion', 'dia_semana', 'asignacion_profesional',
        }
        self.assertFalse(prohibidos.intersection(f.name for f in Cita._meta.concrete_fields))
