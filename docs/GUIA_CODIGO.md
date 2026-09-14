# Guía del código de SASPEL

Esta guía ayuda a encontrar dónde cambiar una funcionalidad. Las rutas parten de la raíz del proyecto. Para requests, respuestas y pruebas manuales de API, consultar [POSTMAN_PRUEBAS.md](POSTMAN_PRUEBAS.md); esta guía lo complementa y no lo reemplaza.

## Qué está implementado

SASPEL tiene login por correo y JWT, consulta de sesión, renovación y paneles por rol. El panel Superadmin permite administrar personas, cambiar su estado, corregir roles administrativos, restablecer claves, consultar estadísticas y gestionar áreas/cargos.

Los modelos de asignaciones profesionales, instrumentos, evaluaciones, disponibilidad y citas ya existen. Su existencia **no implica** que estén implementados los procesos de evaluación inicial, reparto automático de psicólogos, cálculo de resultados o detección de choques de agenda. Las cabeceras de esos modelos indican qué guardan y qué reglas faltan. Los paneles generales de otros roles presentan bienvenida y acceso a sesión.

## Mapa del backend

Todo el código del backend está bajo `backend/`:

| Lugar | Responsabilidad y punto de mantenimiento |
| --- | --- |
| `manage.py` | Arranque de comandos Django. |
| `config/settings.py` | PostgreSQL, aplicaciones instaladas, CORS, zona horaria, validadores de claves y duración JWT. Lee `.env` de la raíz. |
| `config/urls.py` | Monta `/admin/` y `/api/`. |
| `src/domain/value_objects/functional_role.py` | Nombres de roles funcionales. |
| `src/domain/exceptions/superadmin.py` | Errores administrativos que las vistas convierten en HTTP. |
| `src/domain/entities/`, `services/`, `repositories/` | Espacios reservados, actualmente sin implementaciones propias. Los contratos de persistencia actuales están en Application. |
| `src/application/dto/` | Datos de entrada y salida de autenticación, salud y administración. No son tablas. |
| `src/application/ports/input/` | Operaciones que Application ofrece: sesión, salud y principales acciones administrativas. |
| `src/application/ports/output/` | Lo que los casos necesitan del proveedor de identidad y del repositorio administrativo. |
| `src/application/services/auth_identity.py` | Elige rol y dashboard de una identidad verificada. |
| `src/application/use_cases/` | Flujos y reglas de login, identidad, salud, personas y catálogos. |
| `src/infrastructure/auth/` | Consulta y autenticación de cuentas Django; emisión/renovación JWT. |
| `src/infrastructure/dependencies/` | Construye los casos con sus proveedores o repositorios concretos. |
| `src/infrastructure/api/rest/` | URLs, vistas, permisos HTTP y serializers. El permiso administrativo está dentro de `views/superadmin.py`. |
| `src/infrastructure/persistence/django/repositories/administration.py` | Consultas, filtros, paginación, estadísticas, transacciones y escrituras con ORM. |
| `src/infrastructure/persistence/django/models/` | Tablas propias y restricciones declaradas. |
| `src/infrastructure/persistence/django/admin.py` | Registro de modelos en el administrador Django. |
| `src/infrastructure/persistence/django/management/commands/` | Comando de preparación del Superadmin local. |
| `tests/` | Pruebas de arquitectura, casos, API, modelos, comando local y concurrencia. |

El recorrido habitual es: **URL → vista y permiso → serializer → DTO/caso de uso → puerto/repositorio → DTO → respuesta JSON**. Las factorías de `dependencies/` conectan los casos con Infrastructure. El login agrega los tokens en su vista, después de resolver la identidad.

Los puertos evitan que los casos importen Django. Si cambia el almacenamiento, se cambia el adaptador y su factoría, conservando las operaciones, datos, errores y garantías del contrato. Algunas acciones administrativas —rol, activación y catálogos— usan casos concretos sin un puerto de entrada individual; no hay que buscar archivos de contratos que todavía no existen.

## Mapa del frontend

La aplicación Angular está en `frontend/src/`:

| Lugar | Responsabilidad y punto de mantenimiento |
| --- | --- |
| `main.ts` | Arranca `App` con `appConfig`. |
| `environments/` | Base API de compilación normal y desarrollo; selección en `frontend/angular.json`. |
| `app/app.ts`, `app.html` | Contenedor y espacio de navegación. |
| `app/app.config.ts` | Router, HttpClient e interceptor de autenticación. |
| `app/app.routes.ts` | Bienvenida, login y paneles protegidos. |
| `app/core/auth/` | Identidad, almacenamiento de tokens, HTTP de sesión, guards e interceptor. |
| `app/features/welcome/` | Página pública y su ilustración. |
| `app/features/auth/login/` | Pantalla de login, formulario y mensajes. |
| `app/features/dashboards/` | Panel compartido de bienvenida para roles distintos de Superadmin. |
| `app/features/superadmin/superadmin.routes.ts` | Rutas hijas administrativas. |
| `app/features/superadmin/superadmin.service.ts` | Requests administrativos y conversión de errores a texto. |
| `app/features/superadmin/superadmin.models.ts` | Tipos de datos, etiquetas y roles disponibles para alta. |
| `app/features/superadmin/layout/` | Sidebar, cabecera y menú móvil. |
| `app/features/superadmin/dashboard/` | Estadísticas y usuarios recientes. |
| `app/features/superadmin/users/` | Listado, formulario, ficha, cambio de clave y validadores. |
| `app/features/superadmin/institution/` | Pantalla compartida de áreas y cargos. |
| `app/shared/brand/`, `app/features/superadmin/shared/` | Marca y etiqueta de rol reutilizables. |
| `styles.scss`, estilos de cada pantalla y `superadmin.scss` | Aspecto global, local y del módulo administrativo. |

Los componentes presentan datos y enlazan acciones. Los ViewModels cargan información, validan formularios, gestionan estados de carga/error y navegan. Los servicios construyen las solicitudes HTTP. En dashboard Superadmin, catálogos y restablecimiento, componente y ViewModel comparten archivo; en las demás pantallas suelen estar separados.

## Autenticación y cierre de sesión

Para cambiar login, empezar en [authenticate_user.py](../backend/src/application/use_cases/authenticate_user.py). Solicita identidad mediante `AuthProvider`; [django_auth_provider.py](../backend/src/infrastructure/auth/django_auth_provider.py) busca el correo sin distinguir mayúsculas, rechaza duplicados, comprueba clave/actividad y actualiza `last_login`. La cuenta inactiva solo se distingue después de verificar la clave.

[auth_identity.py](../backend/src/application/services/auth_identity.py) resuelve rol y panel. [views/auth.py](../backend/src/infrastructure/api/rest/views/auth.py) valida solicitudes, traduce errores y arma respuestas. En login, `dashboard_path` está separado de `user`; en `me` forma parte de la identidad devuelta. Revisar los tipos Angular antes de cambiar esta diferencia.

[jwt_token_provider.py](../backend/src/infrastructure/auth/jwt_token_provider.py) emite access/refresh y renueva únicamente access. Comprueba que la cuenta siga activa; las duraciones están en `SIMPLE_JWT` de `config/settings.py`. Actualmente no hay rotación ni blacklist de refresh.

En Angular, [auth.service.ts](../frontend/src/app/core/auth/auth.service.ts) mantiene identidad y coordina login/me/refresh. `TokenStorageService` guarda los dos tokens en `sessionStorage`; la identidad se recupera del servidor. `sessionVersion` impide que respuestas tardías restauren una sesión cerrada o reemplazada.

[auth.interceptor.ts](../frontend/src/app/core/auth/auth.interceptor.ts) solo adjunta JWT dentro de la base API y excluye login/refresh. Un 401 provoca una renovación compartida o reutiliza un access que otra petición ya renovó; después reintenta una vez. Si renovación o reintento fallan, cierra la sesión que siga vigente. Conservar las exclusiones y comprobaciones de sesión evita ciclos y afecta directamente las pruebas de concurrencia HTTP.

`logout()` borra tokens e identidad y vuelve al login. **No llama a un endpoint de revocación**. Si se incorpora revocación en el futuro, habrá que coordinar backend, servicio, interceptor y pruebas; cambiar el comentario por sí solo no implementa esa función.

## Personas, roles y permisos

El punto principal de las reglas administrativas es [application/use_cases/superadmin.py](../backend/src/application/use_cases/superadmin.py):

- `CreateUser`: valida rol y clave, normaliza correo y crea cuenta, perfil y grupo en una transacción. Admite NUEVO_TRABAJADOR, PSICOLOGO, ADMIN y SUPERADMIN. TRABAJADOR está reservado para la evaluación inicial aún pendiente.
- `UpdateUser`: admite solo `EDITABLE_FIELDS`; rol, estado y contraseña tienen acciones dedicadas. La habilitación de asignaciones solo se edita para psicólogos.
- `DeactivateUser`, `ActivateUser` y `ChangeUserRole`: conservan registros. La corrección de rol parte de roles administrativos; no implementa la promoción de trabajadores. Si el rol solicitado ya es el actual, devuelve la ficha sin modificarla.
- `protect_superadmin`: evita autooperaciones que quiten acceso y protege al último SUPERADMIN activo. Debe mantenerse dentro de la misma transacción que la escritura.
- `ResetUserPassword`: valida clave y confirmación; el repositorio aplica además los validadores Django y guarda el hash.
- `ManageInstitution`: crea/edita nombre y descripción; las acciones de estado conservan referencias históricas.

El adaptador [repositories/administration.py](../backend/src/infrastructure/persistence/django/repositories/administration.py) es el lugar para modificar consultas. `list_users` pagina de 20 en 20, recientes primero; `summary` calcula cifras reales y cinco usuarios recientes. `check_references` admite conservar un área/cargo inactivo si el vínculo no cambió, pero exige una opción activa al escoger uno nuevo.

`atomic()` bloquea la fila del grupo `SUPERADMIN` en PostgreSQL. El bloqueo serializa escrituras del módulo, incluida la comprobación del último administrador. No quitarlo sin revisar `test_superadmin_concurrency.py`.

La prioridad de identidad es **SUPERADMIN → ADMIN → PSICOLOGO → TRABAJADOR → NUEVO_TRABAJADOR**. Se usa en login, me y la presentación administrativa de cuentas con varios grupos.

Hay una diferencia que debe preservarse o cambiarse de forma coordinada: `is_superuser=True` resuelve identidad SUPERADMIN incluso sin grupo, pero `IsFunctionalSuperadmin`, en `views/superadmin.py`, exige **cuenta activa y grupo SUPERADMIN** para acceder al módulo. El conteo que protege al último administrador también exige ese grupo. Los guards Angular ayudan con la navegación; el permiso del backend decide el acceso a los datos.

Para añadir o renombrar un rol, revisar `functional_role.py`, `ROLE_DASHBOARDS` del backend, preparación de grupos, reglas de alta/transición y permisos; después `core/auth/auth.models.ts`, `superadmin.models.ts`, guards y rutas Angular. Las altas y correcciones administrativas reemplazan las membresías por un grupo; el comando local añade SUPERADMIN conservando otras membresías.

## Modelos y cambios de base de datos

Los modelos propios están en [models/](../backend/src/infrastructure/persistence/django/models/):

| Grupo | Archivos |
| --- | --- |
| Institución y personas | `area_institucional.py`, `cargo_institucional.py`, `perfil_usuario.py` |
| Acompañamiento | `asignacion_profesional.py` |
| Definición de instrumentos | `instrumento_psicologico.py`, `escala_respuesta.py`, `opcion_respuesta.py`, `pregunta_instrumento.py`, `rango_interpretacion.py` |
| Evaluaciones | `asignacion_instrumento.py`, `aplicacion_instrumento.py`, `respuesta_pregunta.py`, `resultado_instrumento.py` |
| Agenda | `disponibilidad_psicologo.py`, `cita.py` |

`User` y `Group` son modelos de Django; `PerfilUsuario` agrega datos personales/laborales. `is_active` controla acceso, `habilitado_asignaciones` la recepción de trabajadores y `tamizaje_resuelto` el indicador de evaluación inicial: no son intercambiables.

Al modificar una tabla en una tarea futura, cambiar el modelo y generar **una migración nueva**. Nunca modificar destructivamente una migración ya aplicada. Para añadir un modelo, crear su archivo e importarlo en `models/__init__.py`; registrarlo en `admin.py` si debe administrarse allí y añadir pruebas de sus restricciones.

`apps.py` conserva el label histórico **`api`** aunque el paquete esté dentro de Infrastructure. Cambiar ese label puede alterar cómo Django reconoce modelos y migraciones. Los archivos históricos están en `persistence/django/migrations/`; esta revisión documental no los modifica ni genera nuevos.

Las restricciones de BD y la validación `full_clean()` no son lo mismo: las escrituras administrativas llaman a esa validación explícitamente. Las reglas todavía pendientes de citas/evaluaciones no deben darse por implementadas al encontrar un campo o un estado disponible.

## Endpoints, pantallas y navegación

Para agregar un endpoint futuro:

1. Ubicar o crear el caso en `application/use_cases/`, con DTO y puertos necesarios.
2. Implementar la operación de persistencia/proveedor en Infrastructure y conectarla en `dependencies/`.
3. Crear serializer del request y vista con autenticación/permisos; traducir resultado y errores.
4. Registrar URL en `auth_urls.py`, `superadmin_urls.py` o un archivo de módulo incluido desde `rest/urls.py`.
5. Añadir pruebas del caso/API y actualizar [POSTMAN_PRUEBAS.md](POSTMAN_PRUEBAS.md).
6. Si hay interfaz, añadir la llamada al servicio y el tipo de respuesta correspondiente.

Para agregar una página Angular, crear el componente dentro de `features/` y su ViewModel si hay estado o acciones. Reutilizar el servicio del módulo, registrar carga en `app.routes.ts` o `superadmin.routes.ts`, asignar guards/datos de ruta y agregar el enlace de navegación que corresponda. En Superadmin, las rutas literales como `personas/nuevo` deben quedar antes de `personas/:id`.

Para modificar el sidebar, ir a [superadmin-layout.html](../frontend/src/app/features/superadmin/layout/superadmin-layout.html). Su TypeScript controla expansión y menú móvil; el SCSS controla apariencia. Los filtros por rol de sus enlaces se resuelven en `superadmin.routes.ts` y `UserListViewModel`, no en una segunda pantalla por rol.

El dashboard Superadmin está en `features/superadmin/dashboard/dashboard.ts`: `cards` define etiquetas y campos mostrados; los totales vienen del servidor. Los paneles generales están en `features/dashboards/dashboard.ts` y `dashboard.viewmodel.ts`. `PANELS` aún contiene texto SUPERADMIN, pero la ruta administrativa principal usa su pantalla propia.

## SI QUIERO CAMBIAR X, ¿DÓNDE VOY?

| Quiero cambiar… | Ir a… |
| --- | --- |
| Comprobación de correo/clave | `backend/src/application/use_cases/authenticate_user.py` y `infrastructure/auth/django_auth_provider.py` |
| Respuesta de login o me | `backend/src/infrastructure/api/rest/views/auth.py`, DTO de auth y `frontend/src/app/core/auth/auth.service.ts` |
| Vencimiento y renovación JWT | `backend/config/settings.py`, `jwt_token_provider.py`, `auth.service.ts`, `auth.interceptor.ts` |
| Cierre de sesión | `frontend/src/app/core/auth/auth.service.ts` y `token-storage.service.ts` |
| Rol y dashboard | `functional_role.py`, `auth_identity.py`, Angular `auth.models.ts`, `role.guard.ts` y rutas |
| Quién puede administrar | `IsFunctionalSuperadmin` en `views/superadmin.py`; revisar guards y pruebas de acceso |
| Registro o edición de personas | `application/use_cases/superadmin.py`, serializers administrativos y `users/user-form.viewmodel.ts` |
| Fortaleza de contraseñas | `validate_password` del caso, `AUTH_PASSWORD_VALIDATORS` y `users/password-validation.ts` |
| Filtros, orden o tamaño de página | `repositories/administration.py:list_users`, `UserFilterSerializer`, DTO y `user-list.viewmodel.ts` |
| Totales del dashboard | Repositorio `summary`, `DashboardSummary`, tipos Angular y `superadmin/dashboard/dashboard.ts` |
| Áreas/cargos | `ManageInstitution`, repositorio, serializers y `institution/institution.ts` |
| Una tabla | `persistence/django/models/`, migración nueva y tests de modelos |
| Un endpoint | Serializer → vista → URLs → caso/repositorio → pruebas y `POSTMAN_PRUEBAS.md` |
| Un caso de uso nuevo | `application/use_cases/`, DTO/ports necesarios y factoría en `infrastructure/dependencies/` |
| Una página nueva | `frontend/src/app/features/`, rutas del módulo y enlaces del layout |
| Sidebar o menú móvil | `features/superadmin/layout/superadmin-layout.{ts,html,scss}` |
| Mensajes de error del panel | `apiError` en `superadmin.service.ts` y ViewModel de la pantalla |
| Marca o bienvenida | `shared/brand/` y `features/welcome/` |
| Cuenta Superadmin local | `management/commands/bootstrap_dev_superadmin.py`; exige DEBUG y cambia clave/permisos de la cuenta configurada |

## Pruebas y comprobaciones

Las pruebas backend están en `backend/tests/`. Arquitectura, salud y casos de autenticación pueden comprobar el núcleo sin persistencia; las pruebas de API/modelos usan BD temporal mediante Django. Concurrencia utiliza `TransactionTestCase` y conexiones PostgreSQL distintas. No sustituirla por una prueba con repositorio simulado si se quiere comprobar el bloqueo real.

Desde `backend/`, con el entorno Python activado:

```powershell
python manage.py check
python manage.py test --noinput
python -m pip check
python manage.py makemigrations --check --dry-run
```

El proyecto usa pruebas `unittest`/Django y no declara pytest en `requirements.txt`. Si se utiliza pytest, se necesitan `pytest` y `pytest-django`, con la configuración Django indicada:

```powershell
python -m pytest --ds=config.settings
```

Las pruebas frontend son `*.spec.ts` junto al código: contenedor, sesión/interceptor, guards, login y Superadmin. Sus requests se simulan; no requieren cuentas reales. Desde `frontend/`:

```powershell
npm run build
npm test -- --watch=false
```

Estos scripts ejecutan `ng build` y `ng test`. Para pruebas manuales de endpoints y permisos usar [POSTMAN_PRUEBAS.md](POSTMAN_PRUEBAS.md).

`docs/sa01-local-check.py` y `sa01-browser-check.cjs` son comprobaciones auxiliares de navegador local: requieren servidores y Playwright/Edge, crean datos temporales en la BD local y después intentan limpiarlos. No son la suite unitaria ni deben importarse como utilidades de la aplicación. Sus requisitos y efectos están documentados en los propios archivos.
