# SA-01 · Panel Superadmin y Personas

Implementado y verificado el 7 de septiembre de 2026. Acceso local:
`http://localhost:4200/dashboard/superadmin` con la cuenta existente.

## Alcance entregado

Layout con sidebar colapsable, submenús, navegación Angular sin recargar,
ruta activa, topbar, identidad autenticada y cierre de sesión. En móvil el menú
abre sobre el contenido y se cierra al navegar o pulsar el fondo.

Inicio muestra ocho indicadores reales —incluye Superadmins— y los últimos
cinco usuarios. Personas permite registro, detalle, edición, filtros, paginación,
activar/desactivar, restablecer contraseña y corregir roles administrativos.
Áreas y Cargos tienen listado, creación, edición y activación/desactivación.

Formularios divididos en Cuenta, Información personal e Información institucional.
Los combos consultan opciones activas reales. Una relación inactiva preexistente
se muestra como actual y no seleccionable para conservar el historial al editar.
Las contraseñas tienen confirmación, mostrar/ocultar y validación local y backend.
Crear otro SUPERADMIN exige un checkbox adicional. Los badges siempre tienen texto.

## Backend y arquitectura

El núcleo usa Python estándar. DRF valida el transporte y delega; no contiene
consultas ORM ni las reglas de creación/transición/protección de personas.

| Capa | Archivos nuevos (relativos a `backend/`) |
| --- | --- |
| Excepciones | `src/domain/exceptions/superadmin.py` |
| DTOs | `src/application/dto/superadmin.py` |
| Puertos de entrada | `src/application/ports/input/administration.py` |
| Puerto de persistencia/unidad de trabajo | `src/application/ports/output/administration.py` |
| Casos de uso | `src/application/use_cases/superadmin.py` |
| Repositorio/adaptador | `src/infrastructure/persistence/django/repositories/administration.py` |
| Composición de dependencias | `src/infrastructure/dependencies/superadmin.py` |
| Serializers | `src/infrastructure/api/rest/serializers/superadmin.py` |
| Vistas y permiso | `src/infrastructure/api/rest/views/superadmin.py` |
| Rutas | `src/infrastructure/api/rest/superadmin_urls.py` |
| Pruebas | `tests/test_superadmin_api.py`, `tests/test_superadmin_concurrency.py` |

Archivos backend modificados:

- `src/infrastructure/api/rest/urls.py`: incluye `/api/superadmin/`.
- `src/infrastructure/auth/django_auth_provider.py`: registra `last_login` al
  autenticar credenciales correctas; el login propio no usaba la vista de SimpleJWT
  encargada de actualizarlo.

DTOs de entrada: `CreateUserCommand`, `UpdateUserCommand`, `ResetPasswordCommand`,
`UserFilters`. Salidas: `UserDTO`, `UserPage`, `InstitutionDTO`, `DashboardSummary`.
Los comandos de contraseña excluyen la clave de su representación `repr`; las
salidas no tienen contraseña ni hash.

Casos de uso: `ListUsers`, `GetUserDetail`, `CreateUser`, `UpdateUser`,
`DeactivateUser`, `ActivateUser`, `ResetUserPassword`, `ChangeUserRole`,
`GetSuperadminDashboardSummary` y `ManageInstitution`.

El puerto `AdministrationRepository` define consultas y escrituras, así como
`atomic()`. `DjangoAdministrationRepository` implementa la transacción y bloquea
la fila estable del grupo SUPERADMIN con `select_for_update`. Así serializa las
escrituras de SA-01, incluida la validación y modificación del último Superadmin
activo, y evita duplicados concurrentes entre solicitudes de este módulo.
Este bloqueo no pretende coordinar escrituras externas realizadas directamente
en SQL o desde otros administradores técnicos.

## Reglas y permisos

- Todos los endpoints administrativos exigen JWT, cuenta activa y pertenencia
  al grupo SUPERADMIN. Un flag `is_superuser` aislado no concede este permiso.
  Se conserva el comportamiento anterior del login para cuentas técnicas.
- Creación: normaliza email, sincroniza username, rechaza correo duplicado sin
  distinguir mayúsculas, aplica validadores de Django y usa `set_password()`.
- Crea cuenta, perfil y exactamente un grupo dentro de una transacción. Si falla
  el perfil o falta el grupo de destino, no quedan registros parciales.
- Roles iniciales: NUEVO_TRABAJADOR, PSICOLOGO, ADMIN y SUPERADMIN. TRABAJADOR
  sigue reservado al proceso de evaluación inicial.
- Solo SUPERADMIN obtiene `is_staff` e `is_superuser`. PSICOLOGO queda habilitado
  para asignaciones por defecto; las demás cuentas no tienen esa función activa.
- PATCH permite identidad y perfil; no acepta rol, contraseña, estado ni tamizaje.
- Corrección de rol: únicamente desde PSICOLOGO, ADMIN o SUPERADMIN, con perfil,
  hacia NUEVO_TRABAJADOR, PSICOLOGO, ADMIN o SUPERADMIN. No hay transiciones de
  trabajadores. La promoción a SUPERADMIN requiere confirmación en la interfaz.
- No se puede auto-desactivar ni retirar el propio rol SUPERADMIN; tampoco
  desactivar o degradar al último activo. La comprobación es transaccional.
- No hay DELETE físico publicado. Desactivación conserva perfil e historial.
- Usuarios antiguos sin perfil aparecen con datos básicos y pueden completarlo
  al editar proporcionando un código empleado.
- Las respuestas administrativas incluyen `Cache-Control: no-store`.

## Endpoints

Prefijo de todos: `/api/superadmin/`.

| Método | Ruta | Función |
| --- | --- | --- |
| GET | `dashboard/summary/` | Totales reales y cinco registros recientes |
| GET, POST | `users/` | Listado paginado / registro |
| GET, PATCH | `users/{id}/` | Detalle / edición |
| POST | `users/{id}/activate/` | Activar |
| POST | `users/{id}/deactivate/` | Desactivar |
| POST | `users/{id}/reset-password/` | Restablecer contraseña |
| POST | `users/{id}/role/` | Corrección administrativa de rol |
| GET, POST | `areas/`, `cargos/` | Listar / crear |
| GET, PATCH | `areas/{id}/`, `cargos/{id}/` | Consultar / editar |
| POST | `areas/{id}/activate/`, `cargos/{id}/activate/` | Activar |
| POST | `areas/{id}/deactivate/`, `cargos/{id}/deactivate/` | Desactivar |

Personas admite `search`, `role`, `active`, `area`, `cargo`, `page`. Página de 20
filas, orden por fecha de registro e ID descendentes. Las categorías del sidebar
reutilizan el mismo endpoint con `role`. Los catálogos admiten `active` y devuelven
un array completo, útil para los combos.

## Frontend y archivos

La feature nueva está bajo `frontend/src/app/features/superadmin/`:

```text
superadmin.models.ts
superadmin.service.ts
superadmin.routes.ts
superadmin.scss
superadmin.spec.ts
layout/
  superadmin-layout.ts
  superadmin-layout.html
  superadmin-layout.scss
dashboard/
  dashboard.ts
shared/
  role-badge.ts
users/
  user-list.ts
  user-list.html
  user-list.viewmodel.ts
  user-form.ts
  user-form.html
  user-form.viewmodel.ts
  user-detail.ts
  user-detail.html
  user-detail.viewmodel.ts
  user-password.ts
  password-validation.ts
institution/
  institution.ts
```

Los componentes pequeños de dashboard, contraseña e institución incluyen su
ViewModel en el mismo archivo; la lógica HTTP permanece en `SuperadminService`.
Áreas y Cargos reutilizan componente y ViewModel con configuración de ruta.
Se utilizan formularios reactivos, signals, cancelación al destruir y `switchMap`
para búsquedas, de modo que una respuesta anterior no sustituya el filtro actual.
No se incorporaron dependencias visuales ni cambios en package.json/lockfiles.

Archivos frontend modificados: `src/app/app.routes.ts` y `src/styles.scss`.
El layout padre sustituye únicamente el panel inicial SUPERADMIN. Mantiene
`authGuard` y `roleGuard`, y agrega `superadminChildGuard` para todas sus hijas.

Rutas bajo `/dashboard/superadmin`:

```text
(inicio)
personas
personas/nuevo
personas/nuevos-trabajadores
personas/trabajadores
personas/psicologos
personas/administradores
personas/:id
personas/:id/editar
personas/:id/password
institucion/areas
institucion/cargos
```

## Menú conceptual y fases posteriores

El menú visible se limita a Inicio, Personas y sus categorías, e Institución.
La extensión conceptual queda organizada por funciones, sin nombres de tablas:

| Sección futura oculta | Funciones previstas |
| --- | --- |
| Personas | Asignaciones profesionales |
| Evaluaciones | Instrumentos, escalas y opciones, preguntas, asignaciones, aplicaciones, resultados |
| Agenda | Citas, disponibilidad |
| Seguimiento | Seguimiento profesional, estado de ánimo, factores psicosociales |
| Alertas y comunicación | Alertas, recomendaciones, notificaciones |
| Seguridad | Políticas, consentimientos, auditoría |
| Reportes | Estadísticas, reportes |
| Configuración | Configuración general futura |

No se desarrollaron estas funciones, BD-05, evaluación inicial, transición a
TRABAJADOR, reparto profesional, gráficas ni exportaciones.

## Verificación ejecutada

| Comprobación | Resultado |
| --- | --- |
| Suite backend completa | **140 pruebas aprobadas** |
| Suite frontend completa | **40 pruebas aprobadas** |
| `manage.py check` | Sin incidencias |
| `pip check` | Sin dependencias rotas |
| `makemigrations --check --dry-run` | Sin cambios detectados |
| `showmigrations --plan` | Todas aplicadas; ninguna pendiente |
| `npm run build` (`ng build`) | Correcto; bundle inicial aprox. 278 kB |
| Arquitectura | Domain y Application sin Django, DRF ni Infrastructure |
| Concurrencia | Dos conexiones intentan desactivar Superadmins mutuamente; una operación se rechaza y permanece un activo |

Backend prueba creación de los cuatro roles y login a sus rutas, hashing, perfil,
grupo único, rollback por fallo de perfil y grupo, duplicados, claves inválidas,
filtros, paginación, edición, correo/username, campos sensibles, desactivación,
reactivación, reset, restricciones Superadmin, permisos y JWT con rol/estado
modificado, resumen real y catálogos sin borrado físico.

Frontend prueba sidebar y submenús, colapso/móvil, guard de hijas para los cinco
roles, listado y filtro por rol, paginación, formularios, contraseñas, confirmación
de Superadmin, edición sin campos sensibles, activar/desactivar y reset.

Comandos desde la raíz (ejecutar npm desde `frontend`):

```powershell
.\.venv\Scripts\python.exe backend/manage.py check
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe backend/manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe backend/manage.py showmigrations --plan
```

Suite backend desde `backend`:

```powershell
..\.venv\Scripts\python.exe manage.py test --noinput --verbosity 1
```

Frontend desde `frontend`:

```powershell
npm.cmd test -- --watch=false
npm.cmd run build
```

## Prueba funcional real en navegador y limpieza

Se ejecutó Edge mediante Playwright, en modo sin ventana, contra Angular en
4200 y Django/PostgreSQL en 8000. Se ingresaron las credenciales existentes de
la cuenta configurada en `SASPEL_DEV_SUPERADMIN_EMAIL` en el formulario de login; no se inyectó una identidad
simulada ni se cambió la contraseña de esa cuenta.

Se comprobó el flujo:

1. Login Superadmin → dashboard con estadísticas reales.
2. Crear Área y Cargo temporales desde la interfaz (la base local no tenía opciones).
3. Registrar NUEVO_TRABAJADOR desde Personas con contraseña, área y cargo.
4. Editar teléfono y comprobar el detalle.
5. Cerrar sesión e ingresar con la nueva cuenta → `/dashboard/nuevo-trabajador`.
6. Verificar 403 del backend para el trabajador y redirección del guard Angular.
7. Regresar como Superadmin, desactivar la cuenta y comprobar login bloqueado.
8. Reactivarla y comprobar login restaurado en el dashboard correcto.
9. Restablecer contraseña desde UI; comprobar rechazo de la anterior y acceso con la nueva.
10. Verificar filtro del sidebar, búsqueda y navegación móvil a 390 px.
11. Comprobar directamente en PostgreSQL User, PerfilUsuario, grupo y vínculos.

Sin errores de JavaScript. No se necesitó una cuenta local de psicólogo: su
creación y redirección están verificadas con API y PostgreSQL de pruebas.

La limpieza eliminó exclusivamente las cuentas aleatorias de prueba, sus
perfiles/membresías y los catálogos temporales, tras comprobar que no había
historial. La base volvió a su estado de datos inicial: **1 usuario original,
0 áreas, 0 cargos**. El último acceso de la cuenta original se actualizó por
los logins reales. Las secuencias de IDs avanzan normalmente y no se reiniciaron.

No se crearon tablas ni migraciones. Se siguen usando:

- `auth_user`
- `auth_group` y la relación existente `auth_user_groups`
- `saspel_perfil_usuario`
- `saspel_area_institucional`
- `saspel_cargo_institucional`

Se comparó el conjunto de tablas antes y después de la prueba, sin diferencias.
Las capturas muestran el momento de la verificación, antes de limpiar los datos.

Evidencias y herramientas nuevas:

- [Resultado del navegador y limpieza](sa01-evidence/result.json).
- Captura de escritorio: `sa01-evidence/desktop.png` (solo local).
- Captura móvil: `sa01-evidence/mobile.png` (solo local).
- Runner y comprobación PostgreSQL: `sa01-local-check.py` (solo local).
- [Recorrido de navegador](sa01-browser-check.cjs).

Las capturas y el runner Python contienen referencias a la cuenta personal de
desarrollo. Se excluyen de Git para conservar la privacidad, sin modificar ni
eliminar esos archivos locales. El resultado JSON y el recorrido de navegador
no contienen credenciales reales y sí se versionan.

Playwright se instaló únicamente en `%TEMP%/saspel-sa01-browser`, fuera de las
dependencias de SASPEL, y utiliza Edge ya instalado. El runner necesita ambos
servidores locales, `DEBUG=True` y las variables locales existentes. Nunca
imprime claves ni almacena trazas de solicitudes con credenciales. Reejecución
solo en la copia original que conserva el runner local (no disponible al clonar):

```powershell
npm.cmd install --prefix "$env:TEMP\saspel-sa01-browser" --no-save --package-lock=false playwright
.\.venv\Scripts\python.exe docs/sa01-local-check.py
```

Documentación modificada: [POSTMAN_PRUEBAS.md](POSTMAN_PRUEBAS.md) incorpora
SUPERADMIN - PERSONAS con todos los endpoints, ejemplos con variables y el flujo
de login/desactivación/reactivación. README enlaza este informe. Esta entrega
termina en SA-01.
