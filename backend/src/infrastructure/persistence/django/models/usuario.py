"""Cuenta SASPEL con UUID, grupos y permisos estándar de Django."""

from django.contrib.auth.models import AbstractUser
from django.db import models

from .auditable import AuditableModel


class Usuario(AuditableModel, AbstractUser):
    debe_cambiar_password = models.BooleanField(default=False)

    class Meta(AbstractUser.Meta):
        db_table = 'saspel_usuario'
        verbose_name = 'usuario SASPEL'
        verbose_name_plural = 'usuarios SASPEL'
