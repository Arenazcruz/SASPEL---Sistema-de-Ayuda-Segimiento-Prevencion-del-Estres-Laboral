"""Publica las operaciones de /api/superadmin/: autentica JWT, exige grupo SUPERADMIN, valida
entrada, llama al caso y convierte DTO a JSON sin caché. Las reglas de negocio están en
application/use_cases/superadmin.py; revisar urls y serializers al cambiar solicitudes.
"""

from dataclasses import asdict
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from src.application.dto.superadmin import CreateUserCommand, ResetPasswordCommand, UpdateUserCommand, UserFilters
from src.application.use_cases import superadmin as cases
from src.domain.exceptions.superadmin import AdministrationError, PersonNotFound
from src.infrastructure.api.rest.serializers.superadmin import (
    InstitutionSerializer, PasswordSerializer, RoleSerializer,
    UserCreateSerializer, UserEditSerializer, UserFilterSerializer,
)
from src.infrastructure.dependencies.superadmin import build_administration


class IsFunctionalSuperadmin(BasePermission):
    """Permiso de todo el módulo: exige cuenta activa y membresía SUPERADMIN;
    is_staff/is_superuser solos no conceden acceso.
    """
    message = 'Esta función requiere el rol SUPERADMIN.'

    def has_permission(self, request, view):
        """Recibe request y vista; consulta el grupo actual y devuelve bool sin escribir. Así un
        token previo no conserva permisos después de quitar el grupo.
        """
        user = request.user
        return bool(user and user.is_authenticated and user.is_active
                    and user.groups.filter(name='SUPERADMIN').exists())


class SuperadminView(APIView):
    """Base que comparte JWT, permiso funcional, traducción de errores y respuesta no-store."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsFunctionalSuperadmin]

    def handle_exception(self, exc):
        """Convierte ausencia en 404 y AdministrationError en 400 por campo; deja los demás
        errores al manejo habitual de DRF.
        """
        if isinstance(exc, PersonNotFound):
            exc = NotFound(str(exc))
        elif isinstance(exc, AdministrationError):
            exc = ValidationError({exc.field: [str(exc)]})
        return super().handle_exception(exc)

    def finalize_response(self, request, response, *args, **kwargs):
        """Añade Cache-Control: no-store a la respuesta final del módulo, incluidas respuestas de
        error.
        """
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'no-store'
        return response

    @staticmethod
    def validated(serializer_class, data, partial=False):
        """Recibe clase serializer, datos y bandera partial; devuelve datos validados o lanza
        error HTTP 400 antes del caso de uso.
        """
        serializer = serializer_class(data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data


class SummaryView(SuperadminView):
    """Sirve los totales reales y usuarios recientes del inicio administrativo."""
    def get(self, request):
        """GET dashboard/summary/: ejecuta GetSuperadminDashboardSummary y devuelve su DTO como
        JSON.
        """
        return Response(asdict(build_administration(cases.GetSuperadminDashboardSummary).execute()))


class UsersView(SuperadminView):
    """Atiende listado y registro en users/; comparte permisos con el resto del módulo."""
    def get(self, request):
        """Valida query params, crea UserFilters y devuelve página calculada por ListUsers sin
        escrituras.
        """
        filters = UserFilters(**self.validated(UserFilterSerializer, request.query_params.dict()))
        return Response(asdict(build_administration(cases.ListUsers).execute(filters)))

    def post(self, request):
        """Valida el alta, crea CreateUserCommand y llama CreateUser; devuelve la ficha con HTTP
        201 o el error traducido.
        """
        command = CreateUserCommand(**self.validated(UserCreateSerializer, request.data))
        return Response(asdict(build_administration(cases.CreateUser).execute(command)), status=201)


class UserDetailView(SuperadminView):
    """Consulta y edición parcial de una persona por ID de cuenta."""
    def get(self, request, user_id):
        """GET users/{id}/: devuelve la ficha de GetUserDetail o 404 si no existe."""
        return Response(asdict(build_administration(cases.GetUserDetail).execute(user_id)))

    def patch(self, request, user_id):
        """Valida campos presentes en el JSON y llama UpdateUser; devuelve la ficha guardada.
        Rol, estado y clave se tramitan en UserActionView.
        """
        changes = self.validated(UserEditSerializer, request.data, partial=True)
        return Response(asdict(build_administration(cases.UpdateUser).execute(UpdateUserCommand(user_id, changes))))


class UserActionView(SuperadminView):
    """Acciones POST dedicadas de rol, estado y restablecimiento; las rutas delimitan los valores
    de action.
    """
    def post(self, request, user_id, action):
        """Recibe user_id/action; valida rol o clave cuando corresponde y pasa request.user.pk
        como actor a las acciones protegidas. Devuelve ficha salvo reset-password, que
        devuelve detail. El else significa deactivate: revisar este despacho al añadir
        acciones a las rutas.
        """
        if action == 'role':
            data = self.validated(RoleSerializer, request.data)
            result = build_administration(cases.ChangeUserRole).execute(user_id, data['role'], request.user.pk)
        elif action == 'reset-password':
            data = self.validated(PasswordSerializer, request.data)
            build_administration(cases.ResetUserPassword).execute(ResetPasswordCommand(user_id, **data))
            return Response({'detail': 'Contraseña restablecida.'})
        elif action == 'activate':
            result = build_administration(cases.ActivateUser).execute(user_id)
        else:
            result = build_administration(cases.DeactivateUser).execute(user_id, request.user.pk)
        return Response(asdict(result))


class InstitutionView(SuperadminView):
    """Comparte listado, alta, edición y activación para areas/cargos según kind recibido de las
    rutas.
    """
    def get(self, request, kind, item_id=None, action=None):
        """Devuelve detalle por ID o listado con filtro active. Una URL de acción devuelve 405;
        consulta ManageInstitution sin escribir.
        """
        if action:
            return Response({'detail': 'Utiliza POST para esta acción.'}, status=405)
        case = build_administration(cases.ManageInstitution)
        if item_id:
            return Response(asdict(case.get(kind, item_id)))
        filters = self.validated(UserFilterSerializer, request.query_params.dict())
        return Response([asdict(item) for item in case.list(kind, filters.get('active'))])

    def post(self, request, kind, item_id=None, action=None):
        """Crea catálogo validado con 201 o activa/desactiva por ID con 200. Rechaza POST de
        edición con 405; el caso controla la transacción.
        """
        case = build_administration(cases.ManageInstitution)
        if action:
            return Response(asdict(case.set_active(kind, item_id, action == 'activate')))
        if item_id:
            return Response({'detail': 'Utiliza PATCH para editar.'}, status=405)
        return Response(asdict(case.save(kind, None, self.validated(InstitutionSerializer, request.data))), status=201)

    def patch(self, request, kind, item_id=None, action=None):
        """Exige ID sin acción, valida nombre/descripcion parciales y devuelve registro
        actualizado; combinación de URL inválida produce 405.
        """
        if item_id is None or action:
            return Response({'detail': 'Selecciona un registro para editar.'}, status=405)
        changes = self.validated(InstitutionSerializer, request.data, partial=True)
        return Response(asdict(build_administration(cases.ManageInstitution).save(kind, item_id, changes)))
