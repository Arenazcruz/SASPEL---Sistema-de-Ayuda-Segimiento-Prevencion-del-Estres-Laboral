"""Este archivo guarda los horarios habituales en los que un psicólogo puede
recibir citas. No crea citas, solo define en qué momentos puede atender.

Por ejemplo, puede indicar que atiende los lunes de 08:00 a 12:00. El día va
de lunes a domingo y la hora de fin debe ser posterior a la de inicio.
No se permite repetir exactamente el mismo bloque para un psicólogo.
Los horarios se interpretan en la zona horaria de la institución. Vacaciones,
feriados y comprobaciones de horarios superpuestos se abordarán más adelante.
Un psicólogo con horarios guardados no se puede borrar.
"""

from django.conf import settings
from django.db import models


class DisponibilidadPsicologo(models.Model):
    """Horario habitual que puede desactivarse cuando deja de estar disponible."""

    class DiaSemana(models.IntegerChoices):
        """Identifica los días desde lunes (0) hasta domingo (6)."""

        LUNES = 0, 'Lunes'
        MARTES = 1, 'Martes'
        MIERCOLES = 2, 'Miércoles'
        JUEVES = 3, 'Jueves'
        VIERNES = 4, 'Viernes'
        SABADO = 5, 'Sábado'
        DOMINGO = 6, 'Domingo'

    # Psicólogo que ofrece este horario de atención.
    psicologo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='disponibilidades_semanales',
        db_index=False,
    )
    # Día en el que se repite el horario cada semana.
    dia_semana = models.PositiveSmallIntegerField(choices=DiaSemana.choices)
    # Hora a partir de la cual puede atender dentro de este bloque.
    hora_inicio = models.TimeField()
    # Hora en la que termina este bloque de atención.
    hora_fin = models.TimeField()
    # Permite dejar de ofrecer este horario sin borrar el registro.
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saspel_disponibilidad_psicologo'
        verbose_name = 'disponibilidad de psicólogo'
        verbose_name_plural = 'disponibilidades de psicólogos'
        # Evita días u horas inválidos y repetir exactamente un horario del psicólogo.
        constraints = [
            models.CheckConstraint(
                condition=models.Q(hora_inicio__lt=models.F('hora_fin')),
                name='saspel_disponibilidad_horas_validas',
            ),
            models.CheckConstraint(
                condition=models.Q(dia_semana__gte=0, dia_semana__lte=6),
                name='saspel_disponibilidad_dia_valido',
            ),
            models.UniqueConstraint(
                fields=['psicologo', 'dia_semana', 'hora_inicio', 'hora_fin'],
                name='saspel_disponibilidad_bloque_unico',
            ),
        ]
        # Facilita consultar qué horarios ofrece un psicólogo en un día de la semana.
        indexes = [
            models.Index(
                fields=['psicologo', 'dia_semana', 'activo'],
                name='saspel_disp_psico_dia_act_idx',
            ),
        ]

    def __str__(self):
        return f'{self.psicologo_id}: {self.get_dia_semana_display()} {self.hora_inicio}–{self.hora_fin}'
