"""Prepara o actualiza la cuenta local mediante SASPEL_DEV_SUPERADMIN_EMAIL/PASSWORD del entorno,
solo con DEBUG=True. Cambia la contraseña y permisos de esa cuenta; no crea PerfilUsuario.
Revisar aquí el arranque local, no usarlo como flujo de registro del panel.
"""

import os
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import transaction


class Command(BaseCommand):
    """Comando bootstrap_dev_superadmin para disponer de acceso administrativo local sin imprimir
    la clave.
    """
    help = 'Crea o actualiza el SUPERADMIN local; solo funciona con DEBUG=True.'

    def handle(self, *args, **options):
        """Valida configuración, busca un correo único y crea/actualiza User en una transacción.
        Activa cuenta y flags Django, reemplaza clave y añade grupo SUPERADMIN conservando
        otros grupos. Rechaza ambigüedad y username ajeno con CommandError; escribe mensaje de
        resultado, sin devolver datos.
        """
        if not settings.DEBUG:
            raise CommandError('Este comando requiere DEBUG=True.')
        email = os.getenv('SASPEL_DEV_SUPERADMIN_EMAIL', '').strip().lower()
        password = os.getenv('SASPEL_DEV_SUPERADMIN_PASSWORD', '')
        try:
            validate_email(email)
        except ValidationError as error:
            raise CommandError('Configura SASPEL_DEV_SUPERADMIN_EMAIL con un correo válido.') from error
        User = get_user_model()
        if not password or len(email) > User._meta.get_field('username').max_length:
            raise CommandError('Revisa las variables locales del superadministrador.')
        with transaction.atomic():
            matches = list(User.objects.filter(email__iexact=email)[:2])
            if len(matches) > 1:
                raise CommandError('Hay varias cuentas con ese correo; resuelve la duplicación primero.')
            if matches:
                user, created = matches[0], False
                if User.objects.filter(username__iexact=email).exclude(pk=user.pk).exists():
                    raise CommandError('El nombre de acceso ya pertenece a otra cuenta.')
            else:
                if User.objects.filter(username__iexact=email).exists():
                    raise CommandError('Ese nombre de acceso pertenece a una cuenta con otro correo.')
                user, created = User.objects.get_or_create(username=email, defaults={'email': email})
            user.username = user.email = email
            user.is_active = user.is_staff = user.is_superuser = True
            user.set_password(password)
            user.save()
            group, _ = Group.objects.get_or_create(name='SUPERADMIN')
            user.groups.add(group)
        action = 'creada' if created else 'actualizada'
        self.stdout.write(self.style.SUCCESS(f'Cuenta SUPERADMIN local {action}: {email}'))
