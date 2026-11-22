# T23 - Asignación Psicólogo-Trabajador

Implementación manual en `feature/asignacion-profesional`, sin integrar a
`develop` ni `main`. Utiliza el modelo `AsignacionProfesional` existente;
no agrega tablas ni migraciones.

## Funcionalidad

En **Superadmin → Personas → Asignaciones profesionales**, ruta
`/dashboard/superadmin/personas/asignaciones-profesionales`:

- Listado paginado de asignaciones, búsqueda por persona y filtro de estado.
- Trabajadores sin vínculo ACTIVA, con búsqueda y paginación propias.
- Psicólogos activos y habilitados, ordenados por cantidad de asignaciones activas.
- Formulario de asignación manual desde un trabajador pendiente.
- Reasignación a un psicólogo diferente, con motivo administrativo obligatorio.
- Finalización con motivo, fecha de cierre e historial conservado.
- Historial de un trabajador accesible desde ambos listados.

La selección manual admite `TRABAJADOR` y `NUEVO_TRABAJADOR` activos. No cambia
su rol ni `tamizaje_resuelto`. El psicólogo debe tener rol funcional `PSICOLOGO`,
cuenta activa, perfil existente y `habilitado_asignaciones=True`. La prioridad
de roles coincide con la administración de personas existente.

La carga cuenta vínculos `ACTIVA`, incluso si posteriormente se desactiva la
cuenta del trabajador. Desactivar acceso no cierra asignaciones implícitamente.
Un psicólogo inhabilitado o inactivo deja de aparecer como receptor disponible;
sus vínculos se siguen viendo en el listado y el historial. Se puede finalizar
un vínculo aunque sus participantes hayan perdido acceso. Para reasignar se
valida nuevamente que el trabajador esté activo y sea elegible.

## Integridad y concurrencia

Cada trabajador admite como máximo un vínculo ACTIVA. Trabajador y psicólogo
deben ser diferentes. Reasignar al mismo profesional se rechaza.

```text
Asignar:   sin ACTIVA → nuevo vínculo ACTIVA
Finalizar: ACTIVA → FINALIZADA + fecha_fin + motivo_fin
Reasignar: ACTIVA → REASIGNADA + fecha_fin + motivo_fin
                   + nuevo vínculo ACTIVA (misma transacción)
```

Las escrituras comparten `atomic()` y el bloqueo del grupo SUPERADMIN del
repositorio administrativo de SA-01. Esto serializa T23 con las ediciones de
rol, acceso y habilitación realizadas por esa API. Las operaciones sobre un
vínculo existente bloquean además su fila con `select_for_update`.
Se conserva la restricción única parcial de la base como última defensa.

El bloqueo compartido prioriza consistencia sobre paralelismo; las escrituras
administrativas se ejecutan una por una. Los escritores SQL externos y Django
Admin no participan en este protocolo. Si en el futuro se sustituyen estos
bloqueos por otros más finos, deben coordinarse ambos módulos y conservarse
las pruebas de concurrencia.

Si falla el alta del nuevo vínculo, se revierte el cierre del anterior.
Una petición repetida sobre una asignación ya cerrada se rechaza; nunca cierra
la nueva asignación por error. No hay endpoint DELETE ni borrado de historial.

## Arquitectura y mantenimiento

| Capa | Archivos principales | Responsabilidad |
| --- | --- | --- |
| Domain | `domain/services/professional_assignment.py` | Elegibilidad, estados y motivo de cierre |
| Application | `application/dto/assignments.py` | Datos mínimos, comandos y páginas |
| Puertos | `application/ports/input/assignments.py`, `output/assignments.py` | Contratos de entrada y persistencia |
| Casos | `application/use_cases/assignments.py` | Asignar, finalizar, reasignar y consultar |
| Repositorio | `infrastructure/persistence/django/repositories/assignments.py` | ORM, filtros, carga y persistencia |
| Adaptador HTTP | `infrastructure/api/rest/serializers/assignments.py`, `views/assignments.py` | Validación de transporte y traducción de DTO |
| Composición | `infrastructure/dependencies/assignments.py` | Construcción de casos con adaptador Django |
| Angular | `features/superadmin/assignments/` | Vista, ViewModel, servicio HTTP y contratos TypeScript |

Las rutas se registran en `superadmin_urls.py` y heredan `SuperadminView`:
JWT, grupo SUPERADMIN, errores 400/404 y `Cache-Control: no-store`.
Domain/Application no importan Django, DRF ni Infrastructure. El repositorio
carga identidades en lote; las listas de asignaciones y pendientes usan 20 filas.

Angular reutiliza el layout, estilos y autenticación existentes. Las lecturas
obsoletas se cancelan con `switchMap`; después de escribir se recargan vínculos,
pendientes y carga. Durante el envío se bloquea la repetición de la acción.
Los rechazos conservan el formulario para corregirlo o cancelar y actualizar.

Los detalles de solicitudes y ejemplos están en
[Postman: T23](POSTMAN_PRUEBAS.md#t23---asignaciones-profesionales).

## Verificación

Desde `backend`, usando el entorno virtual del proyecto:

```powershell
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py test --noinput --verbosity 1
..\.venv\Scripts\python.exe -m pip check
..\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Desde `frontend`:

```powershell
npm.cmd test -- --watch=false
npm.cmd run build
```

Resultados de T23:

- Backend: **165 pruebas aprobadas**, incluidas 25 nuevas de T23.
- Tres pruebas con conexiones PostgreSQL independientes: doble asignación,
  doble reasignación y competencia entre finalizar/reasignar.
- Prueba de rollback al fallar la creación del reemplazo.
- Elegibilidad, activo duplicado, autoasignación, permisos 401/403, token con rol
  retirado, filtros, paginación de 25 filas, carga e historial comprobados.
- Frontend: **50 pruebas aprobadas**, incluidas 10 nuevas de T23 y la comprobación
  del enlace en el menú existente. Compilación de producción correcta.
- Recorrido de UI en Edge sin ventana a 1440 y 390 px, con API simulada y datos
  ficticios: asignar, reasignar, historial, finalizar y menú móvil. Sin errores
  JavaScript ni desbordamiento horizontal de la página. Las tablas anchas tienen
  desplazamiento horizontal propio. Esta revisión visual complementa las pruebas
  API con PostgreSQL; no constituye un recorrido de navegador con backend real.

Las pruebas backend usan una base PostgreSQL temporal que Django crea y elimina.
La revisión de navegador no modifica la base local ni utiliza credenciales reales.

## Alcance pendiente

T23 termina en asignación manual. La asignación automática al finalizar tamizaje,
T24/T25 y la integración de esta rama a `develop`/`main` quedan fuera de esta entrega.
