"""Este archivo comprueba cómo se guardan cuestionarios y evaluaciones de prueba.

Verifica que puedan existir varias versiones, que no se repitan preguntas o
respuestas donde no corresponde y que los resultados sigan vinculados a la
evaluación original. También comprueba que los datos utilizados se conserven.
Usa ejemplos ficticios en una base temporal, sin cargar cuestionarios reales.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from src.infrastructure.persistence.django.models import (
    AplicacionInstrumento,
    AsignacionInstrumento,
    EscalaRespuesta,
    InstrumentoPsicologico,
    OpcionRespuesta,
    PreguntaInstrumento,
    RangoInterpretacion,
    RespuestaPregunta,
    ResultadoInstrumento,
)


class InstrumentDataModelTests(TestCase):
    """Comprueba que se guarden correctamente los datos de una evaluación."""
    @classmethod
    def setUpTestData(cls):
        """Prepara cadena ficticia completa: instrumento, escala, pregunta, rango, asignación,
        aplicación, respuesta y resultado. No carga instrumentos clínicos reales.
        """
        User = get_user_model()
        cls.trabajador = User.objects.create_user(username='trabajador_bd03')
        cls.profesional = User.objects.create_user(username='profesional_bd03')
        cls.instrumento = InstrumentoPsicologico.objects.create(
            codigo='TEST-BD03', nombre='Instrumento ficticio de prueba',
        )
        cls.escala = EscalaRespuesta.objects.create(nombre='Escala ficticia de prueba')
        cls.opcion = OpcionRespuesta.objects.create(
            escala=cls.escala, etiqueta='Opción de prueba', valor=0, orden=1,
        )
        cls.pregunta = PreguntaInstrumento.objects.create(
            instrumento=cls.instrumento, texto='Pregunta ficticia de prueba',
            orden=1, tipo_respuesta='ESCALA', escala=cls.escala,
        )
        cls.rango = RangoInterpretacion.objects.create(
            instrumento=cls.instrumento, nombre='Rango ficticio',
            puntaje_minimo=0, puntaje_maximo=10, orden=1,
        )
        cls.asignacion = AsignacionInstrumento.objects.create(
            trabajador=cls.trabajador, instrumento=cls.instrumento,
            origen='PROFESIONAL', asignado_por=cls.profesional,
        )
        cls.aplicacion = AplicacionInstrumento.objects.create(asignacion=cls.asignacion)
        cls.respuesta = RespuestaPregunta.objects.create(
            aplicacion=cls.aplicacion, pregunta=cls.pregunta, opcion=cls.opcion,
        )
        cls.resultado = ResultadoInstrumento.objects.create(
            aplicacion=cls.aplicacion, puntaje_total=Decimal('5.1250'),
            rango=cls.rango, fecha_calculo=timezone.now(),
        )

    def nueva_aplicacion(self, **asignacion_fields):
        """Prepara otra evaluación de ejemplo para el mismo trabajador u otro indicado."""
        fields = {
            'trabajador': self.trabajador,
            'instrumento': self.instrumento,
            'origen': 'SISTEMA',
        }
        fields.update(asignacion_fields)
        return AplicacionInstrumento.objects.create(
            asignacion=AsignacionInstrumento.objects.create(**fields),
        )

    def test_crear_instrumento_con_version_predeterminada(self):
        self.instrumento.refresh_from_db()
        self.instrumento.full_clean()
        self.assertEqual(self.instrumento.version, '1.0')
        self.assertTrue(self.instrumento.activo)
        self.assertFalse(self.instrumento.es_inicial)
        self.assertEqual(self.instrumento.descripcion, '')
        self.assertEqual(self.instrumento.instrucciones, '')
        self.assertIn('TEST-BD03 / 1.0', str(self.instrumento))

    def test_codigo_y_version_no_pueden_duplicarse(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            InstrumentoPsicologico.objects.create(
                codigo=self.instrumento.codigo, version='1.0', nombre='Duplicado ficticio',
            )

    def test_version_nueva_conserva_referencia_historica(self):
        """Crea una nueva versión y evaluación; el resultado anterior debe seguir apuntando a su
        versión original.
        """
        nueva_version = InstrumentoPsicologico.objects.create(
            codigo=self.instrumento.codigo, version='2.0', nombre='Nueva versión ficticia',
        )
        aplicacion_nueva = self.nueva_aplicacion(instrumento=nueva_version)
        self.resultado.refresh_from_db()
        self.assertEqual(self.resultado.aplicacion.asignacion.instrumento, self.instrumento)
        self.assertEqual(self.resultado.aplicacion.asignacion.instrumento.version, '1.0')
        self.assertEqual(aplicacion_nueva.asignacion.instrumento.version, '2.0')

    def test_instrumentos_distintos_pueden_compartir_version(self):
        otro = InstrumentoPsicologico.objects.create(codigo='TEST-OTRO', nombre='Otro ficticio')
        self.assertEqual(otro.version, self.instrumento.version)

    def test_campos_de_instrumento_obligatorios(self):
        for campo in ('codigo', 'nombre', 'version'):
            fields = {'codigo': 'TEST-NUEVO', 'nombre': 'Prueba', 'version': '1.0'}
            fields[campo] = ''
            with self.subTest(campo=campo), self.assertRaises(ValidationError):
                InstrumentoPsicologico(**fields).full_clean()

    def test_crear_escala(self):
        self.escala.refresh_from_db()
        self.escala.full_clean()
        self.assertTrue(self.escala.activo)
        self.assertEqual(self.escala.descripcion, '')
        self.assertEqual(str(self.escala), self.escala.nombre)

    def test_nombre_escala_no_puede_duplicarse(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            EscalaRespuesta.objects.create(nombre=self.escala.nombre)

    def test_crear_opcion_con_valor_negativo(self):
        opcion = OpcionRespuesta.objects.create(
            escala=self.escala, etiqueta='Otra opción ficticia', valor=-1, orden=0,
        )
        opcion.refresh_from_db()
        opcion.full_clean()
        self.assertEqual(opcion.valor, -1)
        self.assertTrue(opcion.activo)
        self.assertEqual(opcion.escala, self.escala)

    def test_opciones_no_duplican_orden_dentro_de_escala(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            OpcionRespuesta.objects.create(escala=self.escala, etiqueta='Prueba', valor=1, orden=1)

    def test_opciones_no_duplican_valor_dentro_de_escala(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            OpcionRespuesta.objects.create(escala=self.escala, etiqueta='Prueba', valor=0, orden=2)

    def test_otra_escala_permite_mismo_orden_y_valor(self):
        otra = EscalaRespuesta.objects.create(nombre='Otra escala ficticia')
        opcion = OpcionRespuesta.objects.create(escala=otra, etiqueta='Prueba', valor=0, orden=1)
        self.assertNotEqual(opcion.escala, self.opcion.escala)

    def test_crear_pregunta_con_escala(self):
        self.pregunta.refresh_from_db()
        self.pregunta.full_clean()
        self.assertEqual(self.pregunta.instrumento, self.instrumento)
        self.assertEqual(self.pregunta.escala, self.escala)
        self.assertFalse(self.pregunta.invertida)
        self.assertTrue(self.pregunta.obligatoria)
        self.assertTrue(self.pregunta.activo)

    def test_pregunta_permite_escala_opcional(self):
        for orden, tipo in enumerate(PreguntaInstrumento.TipoRespuesta.values, start=2):
            with self.subTest(tipo=tipo):
                pregunta = PreguntaInstrumento.objects.create(
                    instrumento=self.instrumento, texto='Pregunta de prueba',
                    orden=orden, tipo_respuesta=tipo,
                )
                pregunta.full_clean()
                self.assertIsNone(pregunta.escala)

    def test_preguntas_no_duplican_orden_en_instrumento(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            PreguntaInstrumento.objects.create(
                instrumento=self.instrumento, texto='Duplicada', orden=1, tipo_respuesta='TEXTO',
            )

    def test_otro_instrumento_permite_mismo_orden_de_pregunta(self):
        otro = InstrumentoPsicologico.objects.create(codigo='TEST-OTRO', nombre='Otro ficticio')
        pregunta = PreguntaInstrumento.objects.create(
            instrumento=otro, texto='Pregunta de prueba', orden=1, tipo_respuesta='TEXTO',
        )
        self.assertNotEqual(pregunta.instrumento, self.pregunta.instrumento)

    def test_crear_rango(self):
        self.rango.refresh_from_db()
        self.rango.full_clean()
        self.assertEqual(self.rango.instrumento, self.instrumento)
        self.assertEqual(self.rango.interpretacion, '')
        self.assertTrue(self.rango.activo)

    def test_rango_rechaza_minimo_mayor_que_maximo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            RangoInterpretacion.objects.create(
                instrumento=self.instrumento, nombre='Inválido', orden=2,
                puntaje_minimo=20, puntaje_maximo=10,
            )

    def test_rango_permite_limites_iguales(self):
        rango = RangoInterpretacion.objects.create(
            instrumento=self.instrumento, nombre='Puntual ficticio', orden=2,
            puntaje_minimo=-1, puntaje_maximo=-1,
        )
        rango.full_clean()
        self.assertEqual(rango.puntaje_minimo, rango.puntaje_maximo)

    def test_rangos_no_duplican_nombre_en_instrumento(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            RangoInterpretacion.objects.create(
                instrumento=self.instrumento, nombre=self.rango.nombre, orden=2,
                puntaje_minimo=11, puntaje_maximo=20,
            )

    def test_rangos_no_duplican_orden_en_instrumento(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            RangoInterpretacion.objects.create(
                instrumento=self.instrumento, nombre='Otro rango ficticio', orden=1,
                puntaje_minimo=11, puntaje_maximo=20,
            )

    def test_otra_version_permite_mismo_nombre_y_orden_de_rango(self):
        otro = InstrumentoPsicologico.objects.create(
            codigo=self.instrumento.codigo, nombre='Otra versión ficticia', version='2.0',
        )
        rango = RangoInterpretacion.objects.create(
            instrumento=otro, nombre=self.rango.nombre, orden=1,
            puntaje_minimo=0, puntaje_maximo=20,
        )
        self.assertNotEqual(rango.instrumento, self.rango.instrumento)

    def test_crear_asignacion_profesional_de_instrumento(self):
        self.asignacion.refresh_from_db()
        self.asignacion.full_clean()
        self.assertEqual(self.asignacion.estado, 'PENDIENTE')
        self.assertEqual(self.asignacion.asignado_por, self.profesional)
        self.assertIsNotNone(self.asignacion.fecha_asignacion)
        self.assertIsNone(self.asignacion.fecha_limite)
        self.assertEqual(self.trabajador.asignaciones_de_instrumentos.get(), self.asignacion)
        self.assertEqual(self.profesional.asignaciones_de_instrumentos_creadas.get(), self.asignacion)

    def test_asignacion_de_sistema_permite_asignado_por_nulo(self):
        aplicacion = self.nueva_aplicacion()
        aplicacion.asignacion.full_clean()
        self.assertIsNone(aplicacion.asignacion.asignado_por)
        self.assertEqual(aplicacion.asignacion.origen, 'SISTEMA')

    def test_mismo_trabajador_e_instrumento_admiten_evaluaciones_independientes(self):
        self.asignacion.estado = 'COMPLETADA'
        self.asignacion.save()
        nueva = self.nueva_aplicacion()
        self.assertNotEqual(nueva.asignacion_id, self.asignacion.pk)
        self.assertEqual(
            AsignacionInstrumento.objects.filter(
                trabajador=self.trabajador, instrumento=self.instrumento,
            ).count(), 2,
        )

    def test_crear_aplicacion(self):
        self.aplicacion.refresh_from_db()
        self.aplicacion.full_clean()
        self.assertEqual(self.aplicacion.asignacion, self.asignacion)
        self.assertEqual(self.aplicacion.estado, 'INICIADA')
        self.assertIsNone(self.aplicacion.fecha_inicio)
        self.assertIsNone(self.aplicacion.fecha_finalizacion)

    def test_no_permite_dos_aplicaciones_para_asignacion(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            AplicacionInstrumento.objects.create(asignacion=self.asignacion)

    def test_crear_respuesta_con_opcion(self):
        self.respuesta.refresh_from_db()
        self.respuesta.full_clean()
        self.assertEqual(self.respuesta.opcion, self.opcion)
        self.assertEqual(self.respuesta.pregunta, self.pregunta)
        self.assertIsNone(self.respuesta.valor_texto)
        self.assertIsNone(self.respuesta.valor_numerico)
        self.assertIsNone(self.respuesta.valor_booleano)

    def test_persistir_respuestas_texto_numero_y_booleano(self):
        casos = (
            ('TEXTO', 'valor_texto', 'Texto ficticio'),
            ('NUMERO', 'valor_numerico', Decimal('-12.3456')),
            ('BOOLEANO', 'valor_booleano', False),
        )
        for orden, (tipo, campo, valor) in enumerate(casos, start=2):
            with self.subTest(tipo=tipo):
                pregunta = PreguntaInstrumento.objects.create(
                    instrumento=self.instrumento, texto='Pregunta de prueba',
                    orden=orden, tipo_respuesta=tipo,
                )
                respuesta = RespuestaPregunta.objects.create(
                    aplicacion=self.aplicacion, pregunta=pregunta, **{campo: valor},
                )
                respuesta.refresh_from_db()
                respuesta.full_clean()
                self.assertEqual(getattr(respuesta, campo), valor)
                self.assertIsNone(respuesta.opcion)

    def test_no_permite_dos_respuestas_a_pregunta_en_aplicacion(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            RespuestaPregunta.objects.create(aplicacion=self.aplicacion, pregunta=self.pregunta)

    def test_otra_aplicacion_puede_responder_misma_pregunta(self):
        respuesta = RespuestaPregunta.objects.create(
            aplicacion=self.nueva_aplicacion(), pregunta=self.pregunta, opcion=self.opcion,
        )
        self.assertNotEqual(respuesta.aplicacion_id, self.respuesta.aplicacion_id)
        self.assertEqual(self.pregunta.respuestas.count(), 2)

    def test_crear_resultado_preserva_decimal_y_fecha_explicitos(self):
        fecha = self.resultado.fecha_calculo
        self.resultado.refresh_from_db()
        self.resultado.full_clean()
        self.assertEqual(self.resultado.puntaje_total, Decimal('5.1250'))
        self.assertEqual(self.resultado.fecha_calculo, fecha)
        self.assertEqual(self.resultado.rango, self.rango)

    def test_resultado_permite_rango_nulo(self):
        resultado = ResultadoInstrumento.objects.create(
            aplicacion=self.nueva_aplicacion(), puntaje_total=Decimal('0'),
            fecha_calculo=timezone.now(),
        )
        resultado.full_clean()
        self.assertIsNone(resultado.rango)

    def test_no_permite_dos_resultados_para_aplicacion(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ResultadoInstrumento.objects.create(
                aplicacion=self.aplicacion, puntaje_total=Decimal('1'), fecha_calculo=timezone.now(),
            )

    def test_resultado_resuelve_trabajador_instrumento_y_rango_por_relaciones(self):
        resultado = ResultadoInstrumento.objects.select_related(
            'aplicacion__asignacion__trabajador', 'aplicacion__asignacion__instrumento', 'rango',
        ).get(pk=self.resultado.pk)
        with self.assertNumQueries(0):
            self.assertEqual(resultado.aplicacion.asignacion.trabajador, self.trabajador)
            self.assertEqual(resultado.aplicacion.asignacion.instrumento, self.instrumento)
            self.assertEqual(resultado.rango.nombre, self.rango.nombre)
            self.assertEqual(resultado.rango.interpretacion, self.rango.interpretacion)

    def test_modelos_no_duplican_datos_transitivos(self):
        prohibidos = {
            AplicacionInstrumento: {'trabajador', 'instrumento'},
            RespuestaPregunta: {'trabajador', 'instrumento', 'puntaje', 'nombre_pregunta', 'texto_pregunta'},
            ResultadoInstrumento: {'trabajador', 'instrumento', 'nombre_rango', 'interpretacion', 'nivel'},
            AsignacionInstrumento: {'nombre_trabajador', 'nombre_profesional', 'correo', 'nombre_instrumento'},
        }
        for model, campos in prohibidos.items():
            with self.subTest(model=model.__name__):
                self.assertFalse(campos.intersection(f.name for f in model._meta.concrete_fields))

    def test_catalogos_y_usuarios_con_historial_no_se_eliminan(self):
        """Intenta borrar referencias utilizadas por evaluaciones para comprobar conservación de
        historial.
        """
        for registro in (
            self.instrumento, self.escala, self.opcion, self.pregunta, self.rango,
            self.trabajador, self.profesional, self.asignacion, self.aplicacion,
        ):
            with self.subTest(model=type(registro).__name__):
                with self.assertRaises(ProtectedError):
                    type(registro).objects.filter(pk=registro.pk).delete()
        self.assertTrue(RespuestaPregunta.objects.filter(pk=self.respuesta.pk).exists())
        self.assertTrue(ResultadoInstrumento.objects.filter(pk=self.resultado.pk).exists())

    def test_resultado_por_si_solo_protege_aplicacion(self):
        self.respuesta.delete()
        with self.assertRaises(ProtectedError):
            self.aplicacion.delete()
        self.assertTrue(ResultadoInstrumento.objects.filter(pk=self.resultado.pk).exists())

    def test_respuesta_por_si_sola_protege_aplicacion(self):
        self.resultado.delete()
        with self.assertRaises(ProtectedError):
            self.aplicacion.delete()
        self.assertTrue(RespuestaPregunta.objects.filter(pk=self.respuesta.pk).exists())

    def test_tipos_estados_y_origen_invalidos_son_rechazados_por_bd(self):
        for registro, campo in (
            (self.pregunta, 'tipo_respuesta'), (self.asignacion, 'origen'),
            (self.asignacion, 'estado'), (self.aplicacion, 'estado'),
        ):
            with self.subTest(model=type(registro).__name__, campo=campo):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    type(registro).objects.filter(pk=registro.pk).update(**{campo: 'INVALIDO'})

    def test_orden_negativo_es_rechazado_por_bd(self):
        for registro in (self.opcion, self.pregunta, self.rango):
            with self.subTest(model=type(registro).__name__):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    type(registro).objects.filter(pk=registro.pk).update(orden=-1)

    def test_timestamps_automaticos_en_los_nueve_modelos(self):
        for registro in (
            self.instrumento, self.escala, self.opcion, self.pregunta, self.rango,
            self.asignacion, self.aplicacion, self.respuesta, self.resultado,
        ):
            with self.subTest(model=type(registro).__name__):
                registro.refresh_from_db()
                creado = registro.creado_en
                actualizado = registro.actualizado_en
                self.assertIsNotNone(creado)
                registro.save()
                registro.refresh_from_db()
                self.assertEqual(registro.creado_en, creado)
                self.assertGreaterEqual(registro.actualizado_en, actualizado)
