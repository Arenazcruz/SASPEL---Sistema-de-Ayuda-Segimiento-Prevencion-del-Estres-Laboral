from contextlib import contextmanager
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils import timezone

from src.application.dto.responder_evaluacion import (
    EvaluacionDetalle, OpcionEvaluacion, PreguntaEvaluacion, RespuestaEvaluacion, ResultadoEvaluacion,
)
from src.application.services.auth_identity import present_identity
from src.application.services.evaluacion_configurada import contenido_disponible
from src.domain.exceptions.evaluacion import EvaluacionError, EvaluacionNoEncontrada
from src.domain.services.resultado_evaluacion import ItemPuntaje, RangoPuntaje
from src.infrastructure.auth.django_auth_provider import DjangoAuthProvider
from src.infrastructure.persistence.django.models import (
    AplicacionInstrumento, AsignacionInstrumento, EscalaRespuesta, InstrumentoPsicologico,
    PreguntaInstrumento, RespuestaPregunta, ResultadoInstrumento, PerfilUsuario, AsignacionProfesional,
)


def preguntas_disponibles(instrumento_id):
    rows = (PreguntaInstrumento.objects.filter(instrumento_id=instrumento_id, activo=True, deleted=False)
            .select_related('escala').prefetch_related('escala__opciones').order_by('orden', 'pk'))
    return tuple(PreguntaEvaluacion(
        p.pk, p.texto, p.orden, p.tipo_respuesta, p.obligatoria,
        tuple(OpcionEvaluacion(o.pk, o.etiqueta) for o in sorted(
            p.escala.opciones.all(), key=lambda option: option.orden,
        ) if o.activo and not o.deleted)
        if p.tipo_respuesta == 'ESCALA' and p.escala and p.escala.activo and not p.escala.deleted else (),
    ) for p in rows)


class DjangoResponderEvaluacionRepository:
    @staticmethod
    def asignacion(usuario_id, asignacion_id, lock=False):
        rows = AsignacionInstrumento.objects.filter(
            pk=asignacion_id, trabajador_id=usuario_id, deleted=False,
            instrumento__es_inicial=True, instrumento__deleted=False,
        )
        if lock:
            rows = rows.select_for_update(of=('self',))
        row = rows.first()
        if row is None:
            raise EvaluacionNoEncontrada('La evaluación no está disponible.')
        return row

    @contextmanager
    def atomic(self, usuario_id, asignacion_id):
        with transaction.atomic():
            assignment = self.asignacion(usuario_id, asignacion_id, lock=True)
            # T25 también bloquea el instrumento al editar preguntas y las escalas al editar opciones.
            InstrumentoPsicologico.objects.select_for_update().get(pk=assignment.instrumento_id)
            scale_ids = PreguntaInstrumento.objects.filter(instrumento_id=assignment.instrumento_id).values('escala_id')
            list(EscalaRespuesta.objects.select_for_update().filter(pk__in=scale_ids).order_by('pk'))
            yield

    def consultar(self, usuario_id, asignacion_id):
        assignment = self.asignacion(usuario_id, asignacion_id)
        instrument = assignment.instrumento
        questions = preguntas_disponibles(instrument.pk)
        app = AplicacionInstrumento.objects.filter(asignacion=assignment).first()
        answers = ()
        if app:
            answers = tuple(RespuestaEvaluacion(
                r.pregunta_id, r.opcion_id, r.valor_texto,
                str(r.valor_numerico) if r.valor_numerico is not None else None, r.valor_booleano,
            ) for r in app.respuestas.filter(deleted=False, pregunta_id__in=[p.id for p in questions]).order_by('pregunta__orden'))
        return EvaluacionDetalle(
            assignment.pk, instrument.pk, instrument.nombre, instrument.version, instrument.instrucciones,
            assignment.estado, app.pk if app else None,
            ('ANULADA' if app.deleted else app.estado) if app else None,
            app.fecha_inicio if app else None, app.fecha_finalizacion if app else None,
            instrument.activo and contenido_disponible(questions), questions, answers,
        )

    def iniciar(self, usuario_id, asignacion_id):
        assignment = self.asignacion(usuario_id, asignacion_id)
        AplicacionInstrumento.objects.create(
            asignacion=assignment, estado='INICIADA', fecha_inicio=timezone.now(),
            creado_por=str(usuario_id), actualizado_por=str(usuario_id),
        )
        assignment.estado = 'EN_PROGRESO'
        assignment.actualizado_por = str(usuario_id)
        assignment.save(update_fields=['estado', 'actualizado_por'])

    def guardar(self, usuario_id, aplicacion_id, respuestas):
        for answer in respuestas:
            data = dict(opcion_id=answer.opcion_id, valor_texto=answer.valor_texto,
                        valor_numerico=answer.valor_numerico, valor_booleano=answer.valor_booleano)
            empty = all(value is None for value in data.values())
            row = RespuestaPregunta.objects.filter(aplicacion_id=aplicacion_id, pregunta_id=answer.pregunta_id).first()
            if row is None and empty:
                continue
            if row is None:
                row = RespuestaPregunta(aplicacion_id=aplicacion_id, pregunta_id=answer.pregunta_id, creado_por=str(usuario_id))
            for field, value in data.items():
                setattr(row, field, value)
            row.deleted = empty
            row.actualizado_por = str(usuario_id)
            row.full_clean()
            row.save()

    def finalizar(self, usuario_id, asignacion_id, aplicacion_id):
        app = AplicacionInstrumento.objects.get(pk=aplicacion_id)
        app.estado = 'FINALIZADA'
        app.fecha_finalizacion = timezone.now()
        app.actualizado_por = str(usuario_id)
        app.save(update_fields=['estado', 'fecha_finalizacion', 'actualizado_por'])
        assignment = self.asignacion(usuario_id, asignacion_id)
        assignment.estado = 'COMPLETADA'
        assignment.actualizado_por = str(usuario_id)
        assignment.save(update_fields=['estado', 'actualizado_por'])

    def rol(self, usuario_id):
        user = get_user_model().objects.select_for_update().filter(pk=usuario_id, is_active=True, deleted=False).first()
        if user is None:
            raise EvaluacionError('La cuenta ya no está disponible para finalizar la evaluación.')
        return present_identity(DjangoAuthProvider._identity(user)).role

    def datos_calculo(self, aplicacion_id):
        app = AplicacionInstrumento.objects.get(pk=aplicacion_id, deleted=False)
        questions = (app.asignacion.instrumento.preguntas.filter(activo=True, deleted=False)
                     .select_related('escala').prefetch_related('escala__opciones').order_by('orden'))
        answers = {r.pregunta_id: r for r in app.respuestas.filter(deleted=False).select_related('opcion')}
        items = []
        for question in questions:
            answer = answers.get(question.pk)
            if answer is None:
                continue  # Las obligatorias ya fueron verificadas por Application.
            if (question.tipo_respuesta != 'ESCALA' or answer.opcion is None or question.escala is None
                    or answer.opcion.escala_id != question.escala_id):
                raise EvaluacionError('La configuración de la evaluación no permite calcular el resultado.')
            values = tuple(Decimal(o.valor) for o in question.escala.opciones.all() if o.activo and not o.deleted)
            items.append(ItemPuntaje(question.tipo_respuesta, question.invertida, Decimal(answer.opcion.valor), values))
        ranges = tuple(RangoPuntaje(r.pk, r.puntaje_minimo, r.puntaje_maximo)
                       for r in app.asignacion.instrumento.rangos.filter(activo=True, deleted=False))
        return tuple(items), ranges

    def crear_resultado(self, usuario_id, aplicacion_id, puntaje, rango_id):
        row, created = ResultadoInstrumento.objects.get_or_create(aplicacion_id=aplicacion_id, defaults={
            'puntaje_total': puntaje, 'rango_id': rango_id, 'fecha_calculo': timezone.now(),
            'creado_por': str(usuario_id), 'actualizado_por': str(usuario_id),
        })
        if not created and (row.deleted or row.puntaje_total != puntaje or row.rango_id != rango_id):
            raise EvaluacionError('El resultado existente no coincide con esta aplicación.')

    def completar_onboarding(self, usuario_id):
        user = get_user_model().objects.get(pk=usuario_id)
        try:
            profile = PerfilUsuario.objects.select_for_update().get(usuario=user, deleted=False)
        except PerfilUsuario.DoesNotExist:
            raise EvaluacionError('No hay un perfil válido para completar el tamizaje.') from None
        profile.tamizaje_resuelto = True
        profile.actualizado_por = str(usuario_id)
        profile.save(update_fields=['tamizaje_resuelto', 'actualizado_por'])
        worker_group = Group.objects.get(name='TRABAJADOR')
        user.groups.remove(Group.objects.get(name='NUEVO_TRABAJADOR'))
        user.groups.add(worker_group)
        user.actualizado_por = str(usuario_id)
        user.save(update_fields=['actualizado_por'])

    def resultado(self, usuario_id, asignacion_id):
        assignment = self.asignacion(usuario_id, asignacion_id)
        row = (ResultadoInstrumento.objects.select_related('rango').filter(
            aplicacion__asignacion=assignment, aplicacion__estado='FINALIZADA',
            aplicacion__deleted=False, deleted=False,
        ).first())
        if row is None or assignment.estado != 'COMPLETADA':
            return None
        user = get_user_model().objects.get(pk=usuario_id)
        identity = present_identity(DjangoAuthProvider._identity(user))
        profile = PerfilUsuario.objects.filter(usuario=user, deleted=False).first()
        assigned = AsignacionProfesional.objects.filter(trabajador=user, estado='ACTIVA', deleted=False).exists()
        return ResultadoEvaluacion(
            row.aplicacion_id, assignment.instrumento_id, assignment.instrumento.nombre,
            assignment.instrumento.version, row.fecha_calculo, str(row.puntaje_total),
            row.rango.nombre if row.rango else None, row.rango.interpretacion if row.rango else '',
            bool(profile and profile.tamizaje_resuelto), identity.role, identity.dashboard_path,
            'ASIGNADO' if assigned else 'PENDIENTE',
        )

    def resultado_inicial(self, usuario_id):
        assignment = AsignacionInstrumento.objects.filter(
            trabajador_id=usuario_id, instrumento__es_inicial=True, instrumento__deleted=False,
            estado='COMPLETADA', deleted=False, aplicacion__estado='FINALIZADA',
            aplicacion__deleted=False, aplicacion__resultado__deleted=False,
        ).order_by('-aplicacion__resultado__fecha_calculo', '-pk').first()
        if assignment is None:
            raise EvaluacionNoEncontrada('No hay un resultado inicial disponible.')
        return self.resultado(usuario_id, assignment.pk)
