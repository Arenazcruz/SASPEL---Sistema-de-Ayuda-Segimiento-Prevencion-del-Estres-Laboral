"""Implementa AdministrationRepository con consultas Django sobre User, Group, PerfilUsuario,
áreas y cargos de PostgreSQL. Revisar aquí filtros, paginación, estadísticas y escrituras; las
reglas del flujo se encuentran en application/use_cases/superadmin.py.
"""

from contextlib import contextmanager
from dataclasses import asdict
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Case, CharField, Count, Q, Value, When
from src.application.dto.superadmin import DashboardSummary, InstitutionDTO, UserDTO, UserPage
from src.application.services.auth_identity import ROLE_DASHBOARDS
from src.domain.exceptions.superadmin import AdministrationError, PersonNotFound
from src.domain.services.institutional_email import institutional_email
from src.domain.services.primer_acceso import requiere_password_temporal
from src.infrastructure.persistence.django.models import AreaCargo, AreaInstitucional, CargoInstitucional, PerfilUsuario
from src.infrastructure.persistence.django.models import AsignacionInstrumento, InstrumentoPsicologico

User = get_user_model()


class DjangoAdministrationRepository:
    """Traduce datos ORM a DTO y ofrece la transacción que usan las escrituras administrativas."""
    @contextmanager
    def atomic(self):
        """Abre transaction.atomic y bloquea la fila Group SUPERADMIN hasta terminar. Revierte al
        fallar y traduce ValidationError, IntegrityError o falta de grupo a
        AdministrationError. Conservar este bloqueo junto a protect_superadmin evita
        desactivaciones concurrentes que dejen el sistema sin administrador.
        """
        try:
            with transaction.atomic():
                # Un registro estable serializa las escrituras de este módulo, incluso
                # cuando dos administradores intentan desactivarse entre sí.
                Group.objects.select_for_update().get(name='SUPERADMIN')
                yield
        except ValidationError as error:
            detail = getattr(error, 'message_dict', None)
            field = next(iter(detail)) if detail else 'detail'
            messages = detail[field] if detail else error.messages
            if field == '__all__':
                raise AdministrationError('Los datos no cumplen las restricciones de la operación. Revisa duplicados y referencias.') from None
            raise AdministrationError(' '.join(messages), field) from None
        except IntegrityError:
            raise AdministrationError('Los datos ya existen o una referencia dejó de estar disponible.') from None
        except Group.DoesNotExist:
            raise AdministrationError('Falta un rol funcional en la configuración del sistema.') from None

    @staticmethod
    def users():
        # Una subconsulta por grupo evita multiplicar filas en cuentas antiguas
        # que puedan tener varias membresías; conserva la prioridad del login.
        """Devuelve QuerySet con rol funcional por prioridad de ROLE_DASHBOARDS y
        perfil/área/cargo precargados. Las subconsultas evitan duplicar cuentas con varios
        grupos; is_superuser cuenta como SUPERADMIN para presentación. No confundir esta
        resolución con el permiso de acceso del módulo.
        """
        conditions = []
        for role in ROLE_DASHBOARDS:
            query = Q(pk__in=User.objects.filter(groups__name=role).values('pk'))
            if role == 'SUPERADMIN':
                query |= Q(is_superuser=True)
            conditions.append(When(query, then=Value(role.value)))
        return User.objects.annotate(functional_role=Case(
            *conditions, default=Value(None), output_field=CharField(),
        )).select_related('perfil_usuario__area', 'perfil_usuario__cargo')

    @staticmethod
    def institution_dto(item):
        return InstitutionDTO(item.pk, item.nombre, item.descripcion, item.activo)

    def user_dto(self, user):
        """Recibe cuenta anotada por users() y devuelve UserDTO con catálogos anidados. Si falta
        perfil conserva valores por defecto y tiene_perfil=False; no crea el perfil al leer.
        """
        profile = getattr(user, 'perfil_usuario', None)
        data = {}
        if profile:
            data = {name: getattr(profile, name) for name in (
                'codigo_empleado', 'apellido_materno',
                'fecha_nacimiento', 'sexo', 'telefono', 'tamizaje_resuelto',
                'habilitado_asignaciones',
            )}
            data.update(
                area=self.institution_dto(profile.area) if profile.area else None,
                cargo=self.institution_dto(profile.cargo) if profile.cargo else None,
                tiene_perfil=True,
            )
        return UserDTO(
            id=user.pk, email=user.email, first_name=user.first_name, last_name=user.last_name,
            nombre_completo=' '.join(filter(None, (user.first_name, user.last_name, data.get('apellido_materno')))),
            role=user.functional_role, is_active=user.is_active,
            fecha_registro=user.date_joined, last_login=user.last_login, **data,
        )

    def find_user(self, user_id):
        """Busca ID en el QuerySet con rol y perfil; devuelve User ORM o traduce ausencia a
        PersonNotFound.
        """
        try:
            return self.users().filter(deleted=False).exclude(perfil_usuario__deleted=True).get(pk=user_id)
        except User.DoesNotExist:
            raise PersonNotFound('No se encontró la persona.') from None

    def get_user(self, user_id):
        """Recibe ID de cuenta y devuelve UserDTO; si no existe lanza PersonNotFound."""
        return self.user_dto(self.find_user(user_id))

    def list_users(self, filters):
        """Busca por fragmento de correo, nombre, apellido paterno o código; combina rol,
        actividad, área y cargo. Devuelve UserPage de 20 registros, recientes primero, con ID
        como desempate. Cambiar aquí tamaño/orden y revisar navegación del listado Angular.
        """
        query = self.users().filter(deleted=False).exclude(perfil_usuario__deleted=True)
        if filters.search:
            query = query.filter(
                Q(email__icontains=filters.search) | Q(first_name__icontains=filters.search)
                | Q(last_name__icontains=filters.search) | Q(perfil_usuario__codigo_empleado__icontains=filters.search)
            )
        if filters.role == 'ADMINISTRADORES':
            query = query.filter(functional_role__in=['ADMIN', 'SUPERADMIN'])
        elif filters.role:
            query = query.filter(functional_role=filters.role)
        if filters.active is not None:
            query = query.filter(is_active=filters.active)
        if filters.area:
            query = query.filter(perfil_usuario__area_id=filters.area)
        if filters.cargo:
            query = query.filter(perfil_usuario__cargo_id=filters.cargo)
        count, size = query.count(), 20
        start = (filters.page - 1) * size
        if start >= count:
            return UserPage(count, filters.page, size, [])
        return UserPage(count, filters.page, size, [self.user_dto(u) for u in query.order_by('-date_joined', '-pk')[start:start + size]])

    @staticmethod
    def available_email(first_name, last_name):
        """Reserva lógica bajo el bloqueo de atomic(); incluye cuentas inactivas y usernames."""
        sequence = 1
        email = institutional_email(first_name, last_name, sequence)
        while User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).exists():
            sequence += 1
            email = institutional_email(first_name, last_name, sequence)
        return email

    @staticmethod
    def check_references(changes, profile=None):
        """Valida la combinación resultante de un alta o PATCH, sin alterar datos históricos
        cuando no se envían referencias. None permite desvincular ambos campos.
        """
        if not {'area_id', 'cargo_id'} & changes.keys():
            return
        for field, model in (('area_id', AreaInstitucional), ('cargo_id', CargoInstitucional)):
            value = changes.get(field)
            if value is not None and (profile is None or value != getattr(profile, field)):
                if not model.objects.filter(pk=value, activo=True, deleted=False).exists():
                    raise AdministrationError('Selecciona una opción activa y existente.', field)
        area_id = changes.get('area_id', getattr(profile, 'area_id', None))
        cargo_id = changes.get('cargo_id', getattr(profile, 'cargo_id', None))
        if cargo_id is None:
            return
        if area_id is None:
            raise AdministrationError('Selecciona un área antes de elegir el cargo.', 'cargo_id')
        if not AreaCargo.objects.filter(
            area_id=area_id, cargo_id=cargo_id, deleted=False,
            area__activo=True, area__deleted=False, cargo__activo=True, cargo__deleted=False,
        ).exists():
            raise AdministrationError('El cargo no está habilitado para el área seleccionada.', 'cargo_id')

    @staticmethod
    def set_password(user, password):
        """Aplica validadores Django con los datos de la cuenta y establece su hash en memoria.
        No guarda User; el llamador debe persistirlo. Errores se asocian a password.
        """
        try:
            validate_password(password, user)
        except ValidationError as error:
            raise AdministrationError(' '.join(error.messages), 'password') from None
        user.set_password(password)

    def create_user(self, command):
        """Genera correo único y comprueba referencias, guarda User con hash, perfil sin tamizaje resuelto y
        un único grupo. Solo psicólogos conservan habilitado_asignaciones. Devuelve UserDTO;
        atomic() del caso garantiza que un fallo de perfil/grupo revierta también la cuenta.
        """
        email = self.available_email(command.first_name, command.last_name)
        data = asdict(command)
        self.check_references(data)
        user = User(username=email, email=email,
                    first_name=command.first_name, last_name=command.last_name,
                    debe_cambiar_password=requiere_password_temporal(command.role),
                    is_superuser=command.role == 'SUPERADMIN', is_staff=command.role == 'SUPERADMIN')
        self.set_password(user, command.password)
        user.full_clean()
        user.save()
        profile_data = {key: value for key, value in data.items() if key not in (
            'email', 'password', 'first_name', 'last_name', 'role', 'habilitado_asignaciones',
        )}
        profile = PerfilUsuario(usuario=user, **profile_data, tamizaje_resuelto=False,
                                habilitado_asignaciones=command.habilitado_asignaciones if command.role == 'PSICOLOGO' else False)
        profile.full_clean()
        profile.save()
        user.groups.set([Group.objects.get(name=command.role)])
        return self.get_user(user.pk)

    def instrumento_inicial_activo(self):
        return (InstrumentoPsicologico.objects.select_for_update()
                .filter(activo=True, es_inicial=True, deleted=False)
                .values_list('pk', flat=True).first())

    def asegurar_asignacion_inicial(self, usuario_id, instrumento_id):
        # Bloqueo de la cuenta dentro de atomic: serializa reintentos para esta persona.
        User.objects.select_for_update().get(pk=usuario_id)
        if not AsignacionInstrumento.objects.filter(
            trabajador_id=usuario_id, instrumento_id=instrumento_id,
        ).exists():
            AsignacionInstrumento.objects.create(
                trabajador_id=usuario_id, instrumento_id=instrumento_id,
                origen='SISTEMA', estado='PENDIENTE', asignado_por=None,
            )

    def update_user(self, user_id, changes):
        """Actualiza cuenta y perfil desde cambios parciales, conservando email y username.
        Puede completar un perfil ausente si se proporciona código. Guarda solo campos de
        cuenta editados para no sobrescribir last_login concurrente; devuelve UserDTO y
        requiere atomic() del caso.
        """
        user = self.find_user(user_id)
        for name in ('first_name', 'last_name'):
            if name in changes:
                setattr(user, name, changes[name])
        user.full_clean()
        # Solo escribe los campos de cuenta editados: no pisa un last_login concurrente.
        account_fields = set(changes) & {'first_name', 'last_name'}
        if account_fields:
            user.save(update_fields=account_fields)
        profile_changes = {key: value for key, value in changes.items() if key not in ('email', 'first_name', 'last_name')}
        if profile_changes:
            profile = getattr(user, 'perfil_usuario', None)
            if profile is None:
                if not profile_changes.get('codigo_empleado'):
                    raise AdministrationError('Indica un código empleado para completar el perfil ausente.', 'codigo_empleado')
                profile = PerfilUsuario(usuario=user)
            self.check_references(profile_changes, profile)
            for name, value in profile_changes.items():
                setattr(profile, name, value)
            profile.full_clean()
            profile.save()
        return self.get_user(user_id)

    def set_active(self, user_id, active):
        """Guarda el estado de acceso de la cuenta y devuelve UserDTO; la protección
        administrativa queda en el caso de uso.
        """
        user = self.find_user(user_id)
        user.is_active = active
        user.save(update_fields=['is_active'])
        return self.get_user(user_id)

    def set_role(self, user_id, role):
        """Exige perfil, reemplaza todas las membresías y sincroniza is_staff/is_superuser.
        Habilita asignaciones solo para PSICOLOGO y reinicia tamizaje al pasar a
        NUEVO_TRABAJADOR. Devuelve UserDTO; permisos y transiciones se validan antes, en el
        caso.
        """
        user = self.find_user(user_id)
        profile = getattr(user, 'perfil_usuario', None)
        if profile is None:
            raise AdministrationError('Completa el perfil antes de cambiar el rol.')
        user.groups.set([Group.objects.get(name=role)])
        user.is_superuser = user.is_staff = role == 'SUPERADMIN'
        user.save(update_fields=['is_superuser', 'is_staff'])
        profile.habilitado_asignaciones = role == 'PSICOLOGO'
        if role == 'NUEVO_TRABAJADOR':
            profile.tamizaje_resuelto = False
        profile.save(update_fields=['habilitado_asignaciones', 'tamizaje_resuelto', 'actualizado_en'])
        return self.get_user(user_id)

    def active_superadmins(self):
        # Solo cuentan cuentas capaces de pasar el permiso funcional del módulo.
        """Cuenta cuentas activas miembros del grupo SUPERADMIN para proteger el último acceso
        administrativo.
        """
        return User.objects.filter(is_active=True, deleted=False, groups__name='SUPERADMIN').count()

    def reset_password(self, user_id, password):
        """Valida y guarda el hash de la clave por ID; devuelve None y nunca devuelve la
        contraseña.
        """
        user = self.find_user(user_id)
        self.set_password(user, password)
        user.save(update_fields=['password'])

    def summary(self):
        """Agrega totales de cuentas por actividad y rol resuelto y devuelve los cinco registros
        más recientes. Incluye cuentas sin perfil; utiliza la misma prioridad que login y
        listado.
        """
        query = self.users().filter(deleted=False).exclude(perfil_usuario__deleted=True)
        counts = query.aggregate(
            users_total=Count('pk'), active_users=Count('pk', filter=Q(is_active=True)),
            inactive_users=Count('pk', filter=Q(is_active=False)),
            **{name: Count('pk', filter=Q(functional_role=role)) for name, role in (
                ('new_workers', 'NUEVO_TRABAJADOR'), ('workers', 'TRABAJADOR'),
                ('psychologists', 'PSICOLOGO'), ('admins', 'ADMIN'), ('superadmins', 'SUPERADMIN'),
            )},
        )
        return DashboardSummary(**counts, recent_users=[self.user_dto(u) for u in query.order_by('-date_joined', '-pk')[:5]])

    @staticmethod
    def institution_model(kind):
        """Resuelve kind interno areas/cargos al modelo; las rutas controlan los valores
        admitidos.
        """
        return {'areas': AreaInstitucional, 'cargos': CargoInstitucional}[kind]

    def find_institution(self, kind, item_id):
        """Busca ID en el catálogo indicado y devuelve modelo ORM; traduce ausencia a
        PersonNotFound.
        """
        model = self.institution_model(kind)
        try:
            return model.objects.get(pk=item_id, deleted=False)
        except model.DoesNotExist:
            raise PersonNotFound('No se encontró el registro institucional.') from None

    def list_institution(self, kind, active=None, area=None):
        """Consulta áreas/cargos con filtro opcional de activo y devuelve DTO ordenados por
        nombre e ID.
        """
        query = self.institution_model(kind).objects.filter(deleted=False)
        if active is not None:
            query = query.filter(activo=active)
        if active is True:
            query = query.filter(deleted=False)
        if kind == 'cargos' and area is not None:
            query = query.filter(
                activo=True, deleted=False,
                relaciones_area__area_id=area, relaciones_area__deleted=False,
                relaciones_area__area__activo=True, relaciones_area__area__deleted=False,
            ).distinct()
        return [self.institution_dto(item) for item in query.order_by('nombre', 'pk')]

    def get_institution(self, kind, item_id):
        """Devuelve InstitutionDTO por kind (areas/cargos) e ID, o lanza PersonNotFound."""
        return self.institution_dto(self.find_institution(kind, item_id))

    def save_institution(self, kind, item_id, changes):
        """Crea o edita el catálogo y rechaza nombres duplicados sin distinguir mayúsculas.
        Ejecuta full_clean, guarda y devuelve DTO; depende de atomic() del caso para revertir
        errores.
        """
        model = self.institution_model(kind)
        item = self.find_institution(kind, item_id) if item_id else model()
        for name, value in changes.items():
            setattr(item, name, value)
        if model.objects.filter(nombre__iexact=item.nombre).exclude(pk=item.pk).exists():
            raise AdministrationError('Ya existe un registro con este nombre.', 'nombre')
        item.full_clean()
        item.save()
        return self.institution_dto(item)
