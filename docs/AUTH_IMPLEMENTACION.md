# Primera rebanada funcional de SASPEL

Bienvenida → login por correo → Django → rol → panel inicial. Esta fase se
detiene antes de BD-05. Los paneles no incorporan módulos funcionales internos.

## Backend

- Rol puro: `FunctionalRole`, en Domain.
- DTOs: `LoginCommand`, `AuthIdentity`, `AuthenticatedUserDTO`.
- Puertos de entrada: `Authentication`, `CurrentIdentity`.
- Puerto de salida: `AuthProvider`.
- Casos de uso: `AuthenticateUser`, `GetAuthenticatedUser`.
- Resolución de rol y panel: `application/services/auth_identity.py`.
- Adaptadores: `DjangoAuthProvider`, `JWTTokenProvider`.
- Composición: `infrastructure/dependencies/auth.py`.
- Endpoints: `POST /api/auth/login/`, `GET /api/auth/me/`,
  `POST /api/auth/refresh/`. Las rutas técnicas anteriores se conservan.
- Dependencias fijadas: SimpleJWT **5.5.1** y PyJWT **2.13.0**.

El correo se busca sin distinguir mayúsculas. Las coincidencias ambiguas no
seleccionan una cuenta arbitraria. La contraseña se verifica con Django y no
se guarda en el DTO de respuesta, navegador o documentación. Las cuentas sin
rol funcional reciben 403. Las cuentas inactivas reciben 403 únicamente cuando
su contraseña es correcta; de otro modo reciben el mismo 401 genérico.

Prioridad: SUPERADMIN, ADMIN, PSICOLOGO, TRABAJADOR, NUEVO_TRABAJADOR.
`is_superuser=True` implica el rol SUPERADMIN. El comando de bootstrap también
asegura su grupo; login y `/me` no escriben grupos ni actualizan last_login.
Más adelante la gestión de cuentas deberá mantener un solo rol funcional.

## Cuenta local

Se ejecutó una vez `bootstrap_dev_superadmin` para la cuenta de desarrollo
configurada en `SASPEL_DEV_SUPERADMIN_EMAIL`.
La cuenta está activa, pertenece a SUPERADMIN y tiene `is_staff=True` e
`is_superuser=True`. La contraseña se guarda con **PBKDF2-SHA256**, no como
texto plano. Sus variables privadas están exclusivamente en el `.env` local
ignorado; `.env.example` incluye ambos nombres con valores vacíos.

El comando requiere `DEBUG=True`, puede repetirse sin duplicar la cuenta y no
crea perfiles ni otras cuentas demo. Los usuarios de otros roles existen solo
durante las pruebas en una base temporal.

## Frontend

- `core/auth`: contratos de sesión, URL de API, almacenamiento de tokens,
  AuthService, AuthGuard, GuestGuard, RoleGuard e interceptor.
- `features/welcome`: página pública e ilustración decorativa.
- `features/auth/login`: vista de login y LoginViewModel.
- `features/dashboards`: vista compartida y DashboardViewModel para cinco roles.
- `shared/brand`: identidad visual reutilizable.
- Rutas públicas: `/` y `/login` (esta última redirige si ya existe sesión).
- Rutas protegidas: `/dashboard/nuevo-trabajador`, `/dashboard/trabajador`,
  `/dashboard/psicologo`, `/dashboard/admin`, `/dashboard/superadmin`.

Los tokens se guardan en sessionStorage. Se consulta `/me` al restaurar sesión
y al entrar a paneles; no se persiste el rol como autoridad local. El
interceptor solo envía tokens a la API configurada, omite login y refresh y
comparte una renovación entre peticiones simultáneas. El reintento no se repite
indefinidamente. Una respuesta tardía no vuelve a abrir una sesión cerrada.

La página pública marca las funciones futuras como «Próximamente». Se utilizó
CSS y componentes pequeños, sin instalar una biblioteca visual. La ilustración
de crecimiento es decorativa y no representa resultados clínicos.

## Comentarios de persistencia

Los 30 archivos revisados ya recibieron el estilo funcional en la tarea anterior.
En esta fase no se reescribieron: una comparación de archivos confirmó que los
modelos, migraciones, admin y pruebas de persistencia permanecen iguales.

- Modelos: `area_institucional.py`, `cargo_institucional.py`, `perfil_usuario.py`,
  `asignacion_profesional.py`, `instrumento_psicologico.py`, `escala_respuesta.py`,
  `opcion_respuesta.py`, `pregunta_instrumento.py`, `rango_interpretacion.py`,
  `asignacion_instrumento.py`, `aplicacion_instrumento.py`, `respuesta_pregunta.py`,
  `resultado_instrumento.py`, `disponibilidad_psicologo.py`, `cita.py` y `models/__init__.py`.
- Migraciones: `0001_initial.py`, `0002_crear_roles_iniciales.py`,
  `0003_instrumentos_psicologicos.py`, `0004_citas_disponibilidad.py`, `migrations/__init__.py`.
- Registro: `admin.py`, `apps.py`, `persistence/__init__.py`, `django/__init__.py`,
  `repositories/__init__.py`.
- Pruebas: `test_initial_data_model.py`, `test_instrument_data_model.py`,
  `test_appointment_data_model.py` y `tests/__init__.py`.

Los comentarios nuevos siguen el mismo enfoque: qué hace el archivo, cómo se
usa y qué comportamiento queda pendiente, sin explicaciones académicas extensas.

## Verificaciones realizadas

| Verificación | Resultado |
| --- | --- |
| Backend: `manage.py test --noinput` | **120 pruebas aprobadas**; 93 previas y 27 nuevas. |
| Frontend: `ng test --watch=false` | **27 pruebas aprobadas** en cuatro archivos. |
| `manage.py check` | Sin incidencias. |
| `pip check` | Sin dependencias incompatibles. |
| `makemigrations --check --dry-run` | Sin cambios de esquema. |
| Plan de migraciones | Ninguna pendiente de aplicar. |
| Pruebas puras de autenticación y arquitectura con `python -S` | 8 aprobadas, sin cargar Django. |
| `ng build` | Build de producción correcto, dentro de los presupuestos configurados. |
| PostgreSQL | 18.2 conectado; **15 tablas SASPEL y 55 índices**, sin nuevas tablas. |
| Usuarios en la base principal | Únicamente la cuenta local solicitada. |
| Revisión de secretos | La contraseña no aparece en código, documentación ni build. |

## Recorrido comprobado en Chrome

Se levantaron Django en **http://127.0.0.1:8000** y Angular en
**http://localhost:4200**. Se verificó en un navegador real controlado con
Playwright, usando Chrome sin ventana y sin modificar el esquema:

1. Bienvenida pública y navegación a login.
2. Login real con la cuenta solicitada, rol SUPERADMIN y panel de superadministración.
3. Recarga de navegador con identidad recuperada desde `/me`.
4. Intento de abrir el panel de trabajador, redirigido al de superadministración.
5. Entrada a `/login` con sesión activa, redirigida al panel propio.
6. Access realmente expirado, renovación por `/refresh` y recuperación de `/me`.
7. Logout, eliminación de ambos tokens y regreso a `/login`.
8. Intento de reabrir el panel sin sesión, bloqueado por el guard.
9. Bienvenida y login a 390 px de ancho sin desbordamiento horizontal.

No se detectaron errores JavaScript. Las capturas de escritorio y móvil se
inspeccionaron visualmente. Playwright se instaló fuera del proyecto como
herramienta temporal de verificación, sin añadir dependencias a Angular.

## Alcance pendiente

Logout elimina la sesión del navegador, pero no revoca tokens en servidor.
La blacklist, registro, recuperación de contraseña y permisos de futuros módulos
quedan para otras fases. Los guards organizan la navegación; los futuros
endpoints funcionales deberán validar también sus permisos en Django.
BD-05 no se implementó.

La [guía de Postman](POSTMAN_PRUEBAS.md) contiene los contratos, errores,
variables locales y pasos para repetir las pruebas de la API.

## Inventario de archivos de esta fase

Se crearon **47 archivos** y se modificaron **14 archivos existentes**, adem?s del `.env` local privado. No se eliminaron archivos.

### Archivos creados

- `backend/src/application/dto/auth.py`
- `backend/src/application/ports/input/authentication.py`
- `backend/src/application/ports/output/auth_provider.py`
- `backend/src/application/services/auth_identity.py`
- `backend/src/application/use_cases/authenticate_user.py`
- `backend/src/application/use_cases/get_authenticated_user.py`
- `backend/src/domain/value_objects/functional_role.py`
- `backend/src/infrastructure/api/rest/auth_urls.py`
- `backend/src/infrastructure/api/rest/serializers/auth.py`
- `backend/src/infrastructure/api/rest/views/auth.py`
- `backend/src/infrastructure/auth/__init__.py`
- `backend/src/infrastructure/auth/django_auth_provider.py`
- `backend/src/infrastructure/auth/jwt_token_provider.py`
- `backend/src/infrastructure/dependencies/auth.py`
- `backend/src/infrastructure/persistence/django/management/__init__.py`
- `backend/src/infrastructure/persistence/django/management/commands/__init__.py`
- `backend/src/infrastructure/persistence/django/management/commands/bootstrap_dev_superadmin.py`
- `backend/tests/test_auth_api.py`
- `backend/tests/test_auth_use_cases.py`
- `backend/tests/test_bootstrap_dev_superadmin.py`
- `docs/AUTH_IMPLEMENTACION.md`
- `docs/POSTMAN_PRUEBAS.md`
- `frontend/public/saspel-mark.svg`
- `frontend/src/app/core/auth/api-url.ts`
- `frontend/src/app/core/auth/auth.guard.spec.ts`
- `frontend/src/app/core/auth/auth.guard.ts`
- `frontend/src/app/core/auth/auth.interceptor.ts`
- `frontend/src/app/core/auth/auth.models.ts`
- `frontend/src/app/core/auth/auth.service.spec.ts`
- `frontend/src/app/core/auth/auth.service.ts`
- `frontend/src/app/core/auth/role.guard.ts`
- `frontend/src/app/core/auth/token-storage.service.ts`
- `frontend/src/app/features/auth/login/login.html`
- `frontend/src/app/features/auth/login/login.scss`
- `frontend/src/app/features/auth/login/login.spec.ts`
- `frontend/src/app/features/auth/login/login.ts`
- `frontend/src/app/features/auth/login/login.viewmodel.ts`
- `frontend/src/app/features/dashboards/dashboard.ts`
- `frontend/src/app/features/dashboards/dashboard.viewmodel.ts`
- `frontend/src/app/features/welcome/welcome-art.scss`
- `frontend/src/app/features/welcome/welcome-art.ts`
- `frontend/src/app/features/welcome/welcome.html`
- `frontend/src/app/features/welcome/welcome.scss`
- `frontend/src/app/features/welcome/welcome.ts`
- `frontend/src/app/shared/brand/brand.ts`
- `frontend/src/environments/environment.development.ts`
- `frontend/src/environments/environment.ts`

### Archivos modificados

- `.env.example`
- `README.md`
- `backend/config/settings.py`
- `backend/requirements.txt`
- `backend/src/infrastructure/api/rest/urls.py`
- `frontend/angular.json`
- `frontend/src/app/app.config.ts`
- `frontend/src/app/app.html`
- `frontend/src/app/app.routes.ts`
- `frontend/src/app/app.spec.ts`
- `frontend/src/app/app.ts`
- `frontend/src/index.html`
- `frontend/src/styles.scss`
- `frontend/tsconfig.spec.json`

El `.env` local solo recibi? las dos variables del SUPERADMIN; su contenido no se incluye en este informe.
