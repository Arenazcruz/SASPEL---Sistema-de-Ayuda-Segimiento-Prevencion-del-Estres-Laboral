"""Cuenta SASPEL con UUID, grupos y permisos estándar de Django."""

from django.contrib.auth.models import AbstractUser

from .auditable import AuditableModel


class Usuario(AuditableModel, AbstractUser):
    class Meta(AbstractUser.Meta):
        db_table = 'saspel_usuario'
        verbose_name = 'usuario SASPEL'
        verbose_name_plural = 'usuarios SASPEL'
