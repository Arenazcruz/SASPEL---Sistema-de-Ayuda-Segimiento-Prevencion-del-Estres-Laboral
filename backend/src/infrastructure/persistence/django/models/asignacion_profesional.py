"""Este archivo registra qué psicólogo está asignado a cada trabajador.

Se conserva el historial cuando un trabajador cambia de profesional. Por
ejemplo, la asignación anterior puede quedar REASIGNADA y la nueva ACTIVA.
Cada trabajador puede tener como máximo una asignación ACTIVA y nadie puede
asignarse a sí mismo. Los usuarios con asignaciones guardadas no se pueden borrar.
La elección automática del psicólogo se implementará más adelante.
"""

from django.conf import settings
from django.db import models


class AsignacionProfesional(models.Model):
    """Vínculo e historial trabajador/psicólogo; constraints impiden autoasignación y dos
    vínculos activos por trabajador.
    """
    class Estado(models.TextChoices):
        ACTIVA = 'ACTIVA', 'Activa'
        FINALIZADA = 'FINALIZADA', 'Finalizada'
        REASIGNADA = 'REASIGNADA', 'Reasignada'

    # Trabajador que recibe el acompañamiento profesional.
    trabajador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='asignaciones_como_trabajador',
    )
    # Psicólogo responsable de acompañar a este trabajador.
    psicologo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='asignaciones_como_psicologo',
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    # Momento en que terminó esta asignación; puede quedar vacío mientras siga vigente.
    fecha_fin = models.DateTimeField(null=True, blank=True)
    # ACTIVA es la asignación vigente; FINALIZADA o REASIGNADA conservan las anteriores.
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.ACTIVA,
    )
    # Explica por qué terminó el vínculo, por ejemplo un cambio de profesional.
    motivo_fin = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saspel_asignacion_profesional'
        verbose_name = 'asignación profesional'
        verbose_name_plural = 'asignaciones profesionales'
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(trabajador=models.F('psicologo')),
                name='saspel_asignacion_usuarios_distintos',
            ),
            models.UniqueConstraint(
                fields=['trabajador'],
                condition=models.Q(estado='ACTIVA'),
                name='saspel_una_asignacion_activa_por_trabajador',
            ),
            models.CheckConstraint(
                condition=models.Q(estado__in=['ACTIVA', 'FINALIZADA', 'REASIGNADA']),
                name='saspel_asignacion_estado_valido',
            ),
        ]

    def __str__(self):
        return f'{self.trabajador_id} → {self.psicologo_id} ({self.estado})'
