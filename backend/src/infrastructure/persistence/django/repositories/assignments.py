"""Adaptador T23 sobre las tablas existentes. No borra vínculos ni altera roles/tamizaje."""

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from src.application.dto.assignments import (
    AssignmentDTO, AssignmentPage, AssignmentPerson, PsychologistLoad, WorkerPage,
)
from src.domain.exceptions.superadmin import PersonNotFound
from src.domain.services.professional_assignment import WORKER_ROLES
from src.infrastructure.persistence.django.models import AsignacionProfesional
from src.infrastructure.persistence.django.repositories.administration import DjangoAdministrationRepository

User = get_user_model()
PAGE_SIZE = 20


class DjangoAssignmentRepository:
    """Comparte el bloqueo SUPERADMIN con SA-01 para serializar escrituras administrativas.

    Así se coordinan alta/reasignación con cambios de rol, acceso y habilitación.
    La restricción única de BD sigue siendo la última defensa frente a escritores
    externos. SQL directo y Django Admin no participan en este protocolo de bloqueo.
    """
    def __init__(self):
        self.administration = DjangoAdministrationRepository()

    def atomic(self):
        return self.administration.atomic()

    @staticmethod
    def person_dto(user):
        profile = getattr(user, 'perfil_usuario', None)
        name = ' '.join(filter(None, (user.first_name, user.last_name,
                                      profile.apellido_materno if profile else '')))
        return AssignmentPerson(
            user.pk, name or user.email, user.email,
            profile.codigo_empleado if profile else '', user.functional_role,
            user.is_active, bool(profile and profile.habilitado_asignaciones),
        )

    def get_person(self, user_id):
        return self.person_dto(self.administration.find_user(user_id))

    def assignment_dtos(self, rows):
        """Carga identidades en lote para evitar una consulta por fila del historial."""
        rows = list(rows)
        ids = {pk for row in rows for pk in (row.trabajador_id, row.psicologo_id)}
        people = {user.pk: self.person_dto(user) for user in self.administration.users().filter(pk__in=ids)}
        return [AssignmentDTO(
            row.pk, people[row.trabajador_id], people[row.psicologo_id],
            row.fecha_asignacion, row.fecha_fin, row.estado, row.motivo_fin,
        ) for row in rows]

    def get_assignment(self, assignment_id):
        try:
            row = AsignacionProfesional.objects.select_for_update().get(pk=assignment_id)
        except AsignacionProfesional.DoesNotExist:
            raise PersonNotFound('La asignación no existe.') from None
        return self.assignment_dtos([row])[0]

    def list_assignments(self, filters):
        rows = AsignacionProfesional.objects.all()
        for key in ('estado', 'trabajador_id', 'psicologo_id'):
            if value := getattr(filters, key):
                rows = rows.filter(**{key: value})
        if filters.search:
            people = self.search_people(self.administration.users(), filters.search).values('pk')
            rows = rows.filter(Q(trabajador_id__in=people) | Q(psicologo_id__in=people))
        count = rows.count()
        start = (filters.page - 1) * PAGE_SIZE
        rows = rows.order_by('-fecha_asignacion', '-pk')[start:start + PAGE_SIZE]
        return AssignmentPage(count, filters.page, PAGE_SIZE, self.assignment_dtos(rows))

    @staticmethod
    def search_people(users, search):
        return users.filter(
            Q(email__icontains=search) | Q(first_name__icontains=search)
            | Q(last_name__icontains=search) | Q(perfil_usuario__apellido_materno__icontains=search)
            | Q(perfil_usuario__codigo_empleado__icontains=search),
        )

    def unassigned_workers(self, search, page):
        active_workers = AsignacionProfesional.objects.filter(estado='ACTIVA').values('trabajador_id')
        users = self.administration.users().filter(is_active=True, functional_role__in=WORKER_ROLES)
        users = self.search_people(users.exclude(pk__in=active_workers), search)
        count = users.count()
        start = (page - 1) * PAGE_SIZE
        users = users.order_by('first_name', 'last_name', 'pk')[start:start + PAGE_SIZE]
        return WorkerPage(count, page, PAGE_SIZE, [self.person_dto(user) for user in users])

    def psychologist_loads(self):
        users = self.administration.users().filter(
            functional_role='PSICOLOGO', is_active=True, perfil_usuario__habilitado_asignaciones=True,
        ).annotate(active_workers=Count(
            'asignaciones_como_psicologo', filter=Q(asignaciones_como_psicologo__estado='ACTIVA'),
        )).order_by('active_workers', 'first_name', 'last_name', 'pk')
        return [PsychologistLoad(self.person_dto(user), user.active_workers) for user in users]

    def has_active_assignment(self, worker_id):
        return AsignacionProfesional.objects.filter(trabajador_id=worker_id, estado='ACTIVA').exists()

    def create_assignment(self, worker_id, psychologist_id):
        row = AsignacionProfesional.objects.create(trabajador_id=worker_id, psicologo_id=psychologist_id)
        return self.assignment_dtos([row])[0]

    def close_assignment(self, assignment_id, state, reason):
        # El caso comprueba ACTIVA bajo el bloqueo compartido antes de llegar aquí.
        row = AsignacionProfesional.objects.get(pk=assignment_id)
        row.estado, row.motivo_fin, row.fecha_fin = state, reason, timezone.now()
        row.save(update_fields=['estado', 'motivo_fin', 'fecha_fin', 'actualizado_en'])
        return self.assignment_dtos([row])[0]
