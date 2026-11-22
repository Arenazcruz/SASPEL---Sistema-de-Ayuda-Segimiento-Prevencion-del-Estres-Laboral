from django.db import models
from .auditable import AuditableModel


class ReglaAlerta(AuditableModel):
    nombre = models.CharField(max_length=150)
    rango = models.ForeignKey('RangoInterpretacion', on_delete=models.PROTECT)
    nivel = models.CharField(max_length=10, choices=[('BAJA','Baja'),('MEDIA','Media'),('ALTA','Alta')])
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = 'saspel_regla_alerta'
        constraints = [models.UniqueConstraint(fields=['rango'], condition=models.Q(activa=True,deleted=False), name='saspel_regla_rango_activa_unica')]


class Alerta(AuditableModel):
    regla = models.ForeignKey(ReglaAlerta, on_delete=models.PROTECT)
    resultado = models.ForeignKey('ResultadoInstrumento', on_delete=models.PROTECT)
    estado = models.CharField(max_length=12, default='ABIERTA', choices=[('ABIERTA','Abierta'),('EN_ATENCION','En atención'),('CERRADA','Cerrada')])

    class Meta:
        db_table = 'saspel_alerta'
        constraints = [models.UniqueConstraint(fields=['regla','resultado'], name='saspel_alerta_evento_unico')]
        ordering = ['-creado_en','-pk']


class AccionAlerta(AuditableModel):
    alerta = models.ForeignKey(Alerta, on_delete=models.PROTECT, related_name='acciones')
    estado = models.CharField(max_length=12)
    observacion = models.TextField()

    class Meta:
        db_table = 'saspel_accion_alerta'
        ordering = ['creado_en','pk']
