"""Identidad y auditoría comunes a las entidades propias de SASPEL."""

import uuid

from django.db import models


class AuditableModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creado_en = models.DateTimeField(auto_now_add=True, db_column='Time_Create')
    actualizado_en = models.DateTimeField(auto_now=True, db_column='Time_Update')
    creado_por = models.CharField(max_length=150, default='SYSTEM', db_column='User_Create')
    actualizado_por = models.CharField(max_length=150, default='SYSTEM', db_column='User_Update')
    deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Las escrituras parciales también deben actualizar su fecha de auditoría.
        fields = kwargs.get('update_fields')
        if fields:
            kwargs['update_fields'] = set(fields) | {'actualizado_en'}
        return super().save(*args, **kwargs)
