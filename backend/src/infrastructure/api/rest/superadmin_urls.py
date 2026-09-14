"""Publica resumen, personas, acciones y catálogos bajo /api/superadmin/. Los bucles fijan
action/kind que consumen las vistas; cambiar sus valores requiere revisar el despacho y
SuperadminService. No hay borrado físico publicado.
"""

from django.urls import path
from src.infrastructure.api.rest.views.assignments import (
    AssignmentsView, FinishAssignmentView, PsychologistLoadsView, ReassignWorkerView, UnassignedWorkersView,
)
from src.infrastructure.api.rest.views.superadmin import InstitutionView, SummaryView, UserActionView, UserDetailView, UsersView

urlpatterns = [
    path('assignments/', AssignmentsView.as_view()),
    path('assignments/unassigned-workers/', UnassignedWorkersView.as_view()),
    path('assignments/psychologists/', PsychologistLoadsView.as_view()),
    path('assignments/<int:assignment_id>/finish/', FinishAssignmentView.as_view()),
    path('assignments/<int:assignment_id>/reassign/', ReassignWorkerView.as_view()),
    path('dashboard/summary/', SummaryView.as_view()),
    path('users/', UsersView.as_view()),
    path('users/<int:user_id>/', UserDetailView.as_view()),
]
for action in ('activate', 'deactivate', 'reset-password', 'role'):
    urlpatterns.append(path(f'users/<int:user_id>/{action}/', UserActionView.as_view(), {'action': action}))
for kind in ('areas', 'cargos'):
    urlpatterns += [
        path(f'{kind}/', InstitutionView.as_view(), {'kind': kind}),
        path(f'{kind}/<int:item_id>/', InstitutionView.as_view(), {'kind': kind}),
    ]
    for action in ('activate', 'deactivate'):
        urlpatterns.append(path(f'{kind}/<int:item_id>/{action}/', InstitutionView.as_view(), {'kind': kind, 'action': action}))
