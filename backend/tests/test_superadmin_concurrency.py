"""Prueba el bloqueo real con conexiones PostgreSQL distintas y escrituras simultáneas."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import close_old_connections, connections
from django.test import TransactionTestCase
from src.application.dto.superadmin import CreateUserCommand
from src.application.use_cases.superadmin import CreateUser, DeactivateUser
from src.domain.exceptions.superadmin import AdministrationError
from src.infrastructure.dependencies.superadmin import build_administration


class SuperadminConcurrencyTests(TransactionTestCase):
    """Usa transacciones y conexiones PostgreSQL separadas para ejercitar el bloqueo real del
    repositorio.
    """
    def test_concurrent_creation_allocates_distinct_emails(self):
        Group.objects.get_or_create(name='SUPERADMIN')
        Group.objects.get_or_create(name='NUEVO_TRABAJADOR')
        start = Barrier(2)

        def create(index):
            close_old_connections()
            try:
                start.wait(timeout=10)
                command = CreateUserCommand(password='Concurrent-safe-827!', first_name='Jesús Gabriel',
                                            last_name='Cruz', apellido_materno='Lavadenz',
                                            codigo_empleado=f'CON-{index}', role='NUEVO_TRABAJADOR')
                return build_administration(CreateUser).execute(command).email
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(create, range(2)))
        self.assertCountEqual(results, ['jesus.cruz@saspel.com', 'jesus.cruz2@saspel.com'])

    def test_two_superadmins_cannot_deactivate_each_other_concurrently(self):
        """Lanza dos desactivaciones cruzadas al mismo tiempo; una debe prosperar y otra proteger
        al administrador restante. Mantener TransactionTestCase y conexiones por hilo: una
        transacción compartida no prueba esta garantía.
        """
        group, _ = Group.objects.get_or_create(name='SUPERADMIN')
        users = []
        for index in range(2):
            user = get_user_model().objects.create(username=f'concurrent-{index}', is_superuser=True)
            user.groups.add(group)
            users.append(user.pk)
        start = Barrier(2)

        def deactivate(actor, target):
            close_old_connections()
            try:
                start.wait(timeout=10)
                try:
                    build_administration(DeactivateUser).execute(target, actor)
                    return 'deactivated'
                except AdministrationError:
                    return 'protected'
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda pair: deactivate(*pair), [users, list(reversed(users))]))
        self.assertCountEqual(results, ['deactivated', 'protected'])
        self.assertEqual(get_user_model().objects.filter(is_active=True, groups=group).count(), 1)
