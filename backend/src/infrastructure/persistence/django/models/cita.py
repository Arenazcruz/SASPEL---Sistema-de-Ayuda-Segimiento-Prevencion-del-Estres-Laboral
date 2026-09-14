"""Este archivo maneja las citas entre trabajadores y psicólogos.
Una cita puede comenzar como solicitud, luego ser confirmada, completada,
cancelada, rechazada o reprogramada.

Guarda quiénes participan, quién la solicitó, su horario y el motivo. Para una
futura reprogramación se creará otra cita vinculada a la anterior, conservando
el horario original. La cita debe terminar después de comenzar; trabajador y
psicólogo deben ser diferentes, y una cita no puede señalarse a sí misma como
origen. Los usuarios y las citas anteriores referenciados se conservan.

Más adelante se comprobarán permisos, disponibilidad y choques de horarios.
Las notas de atención psicológica pertenecerán al módulo de seguimiento.
"""

from django.conf import settings
from django.db import models


class Cita(models.Model):
    """Cita solicitada entre un trabajador y un psicólogo."""

    class Prioridad(models.TextChoices):
        """Indica la prioridad elegida para la cita."""

        BAJA = 'BAJA', 'Baja'
        MEDIA = 'MEDIA', 'Media'
        ALTA = 'ALTA', 'Alta'

    class Estado(models.TextChoices):
        """Indica si la cita está solicitada, confirmada, completada o cerrada.

        REPROGRAMADA identifica una cita reemplazada por otra con un nuevo horario.
        """

        SOLICITADA = 'SOLICITADA', 'Solicitada'
        CONFIRMADA = 'CONFIRMADA', 'Confirmada'
        COMPLETADA = 'COMPLETADA', 'Completada'
        CANCELADA = 'CANCELADA', 'Cancelada'
        RECHAZADA = 'RECHAZADA', 'Rechazada'
        REPROGRAMADA = 'REPROGRAMADA', 'Reprogramada'

    # Trabajador que recibirá la atención.
    trabajador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='citas_como_trabajador', db_index=False,
    )
    # Psicólogo encargado de atender esta cita.
    psicologo = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='citas_como_psicologo', db_index=False,
    )
    # Persona que originó la solicitud: puede ser un participante u otra persona autorizada más
    # adelante.
    solicitada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='citas_solicitadas',
    )
    # Fecha y hora previstas para comenzar la cita.
    fecha_inicio = models.DateTimeField()
    # Fecha y hora previstas para terminar la cita.
    fecha_fin = models.DateTimeField()
    # Razón por la que se solicita la atención.
    motivo = models.TextField()
    # Prioridad elegida para la cita; comienza en MEDIA.
    prioridad = models.CharField(max_length=5, choices=Prioridad.choices, default=Prioridad.MEDIA)
    # Comienza como SOLICITADA; los cambios de estado se gestionarán más adelante.
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.SOLICITADA)
    # Razón de cancelación, rechazo o cierre; no se utiliza para notas psicológicas.
    motivo_cierre = models.TextField(blank=True)
    # Cita anterior que dio lugar a esta reprogramación; así se conserva su horario original.
    cita_origen = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True,
        related_name='reprogramaciones',
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saspel_cita'
        verbose_name = 'cita'
        verbose_name_plural = 'citas'
        # Evita citas con fechas, participantes, origen, estado o prioridad no permitidos.
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_inicio__lt=models.F('fecha_fin')),
                name='saspel_cita_fechas_validas',
            ),
            models.CheckConstraint(
                condition=~models.Q(trabajador=models.F('psicologo')),
                name='saspel_cita_usuarios_distintos',
            ),
            models.CheckConstraint(
                condition=models.Q(cita_origen__isnull=True) | ~models.Q(cita_origen=models.F('pk')),
                name='saspel_cita_origen_distinto',
            ),
            models.CheckConstraint(
                condition=models.Q(estado__in=[
                    'SOLICITADA', 'CONFIRMADA', 'COMPLETADA',
                    'CANCELADA', 'RECHAZADA', 'REPROGRAMADA',
                ]),
                name='saspel_cita_estado_valido',
            ),
            models.CheckConstraint(
                condition=models.Q(prioridad__in=['BAJA', 'MEDIA', 'ALTA']),
                name='saspel_cita_prioridad_valida',
            ),
        ]
        # Facilita buscar la agenda de cada participante por fecha y estado.
        # La detección de choques de horarios se implementará más adelante.
        indexes = [
            models.Index(
                fields=['psicologo', 'fecha_inicio', 'estado'],
                name='saspel_cita_psi_fecha_est_idx',
            ),
            models.Index(
                fields=['trabajador', 'fecha_inicio', 'estado'],
                name='saspel_cita_trab_fecha_est_idx',
            ),
        ]

    def __str__(self):
        return f'Cita {self.pk}: {self.trabajador_id} → {self.psicologo_id} ({self.estado})'
