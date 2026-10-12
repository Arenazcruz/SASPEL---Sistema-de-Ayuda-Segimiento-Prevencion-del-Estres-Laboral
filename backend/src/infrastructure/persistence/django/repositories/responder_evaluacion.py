from contextlib import contextmanager

from django.db import transaction
from django.utils import timezone

from src.application.dto.responder_evaluacion import (
    EvaluacionDetalle, OpcionEvaluacion, PreguntaEvaluacion, RespuestaEvaluacion,
)
from src.application.services.evaluacion_configurada import contenido_disponible
from src.domain.exceptions.evaluacion import EvaluacionNoEncontrada
from src.infrastructure.persistence.django.models import (
    AplicacionInstrumento, AsignacionInstrumento, EscalaRespuesta, InstrumentoPsicologico,
    PreguntaInstrumento, RespuestaPregunta,
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
