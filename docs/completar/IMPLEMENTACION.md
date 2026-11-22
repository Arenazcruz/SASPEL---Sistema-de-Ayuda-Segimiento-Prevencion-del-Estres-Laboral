# Implementación y decisiones técnicas

## Capas y contratos

Se extendió la arquitectura existente. `src/domain/services` contiene las reglas
de transición, edición de versiones y evolución; `src/application/use_cases`
orquesta permisos y transacciones mediante `ports/output`; Infrastructure
implementa ORM, JWT, serializers y vistas. No se añadieron dependencias de Django
al núcleo. Los nuevos servicios Angular consumen la API y los ViewModels
administran carga, validación, vacío, errores y confirmación. El contexto inyectado
de administración permite reutilizar pantallas sin duplicar el CRUD.

No se incorporaron microservicios, colas, IA, dependencias de gráficos ni código
PHP. Las recomendaciones son texto escrito por un profesional; las tendencias
son diferencias entre resultados, no inferencias clínicas.

| Flujo / referencia conceptual | Implementación SASPEL y garantías |
| --- | --- |
| T46, AppointmentController | `citas` en dominio/caso/repositorio/vista y ViewModel Angular. Estado original REPROGRAMADA; sucesora CONFIRMADA con `cita_origen`, razón y horario nuevo. Revalida profesional activo, disponibilidad y solapamiento; una transacción conserva historia y evita sucesoras simultáneas. |
| T47, AssignTestController + AssignedTestsController | `instrument_assignments`, resolución con `inicial=False`, feature `instrumentos`. Solo trabajador propio o profesional asignado; Superadmin puede asignar sin leer respuestas. Instrumento activo no inicial, configurado y sin otro pendiente de esa versión. Fecha límite opcional futura. No repite transición de rol/asignación profesional. |
| Versiones, InstrumentService | `version_instrumento`, repositorios `instruments` e `instrument_content`: una versión con aplicaciones conserva metadatos, preguntas, opciones, valores y orden; los cambios de contenido requieren versión nueva. Se conserva activación/desactivación funcional. |
| T48, TestProfesionalController | `recomendaciones` en puerto/caso/repositorio/vista/feature. Vinculadas a seguimiento; autor desde sesión; texto hasta 5000 caracteres. PENDIENTE → EN_PROGRESO → COMPLETADA, o cancelación admitida; estados terminales no se reabren. Solo profesional con asignación vigente. |
| T49, TestHistoryController y vistas de evolución | `evolucion`: solo aplicaciones finalizadas válidas; agrupación por UUID de instrumento y versión; fecha ordenada, filtro de periodo, tabla y gráfico accesible. Tendencia = último − primero; un punto SIN_COMPARACION. No mezcla escalas ni reescribe evaluaciones. |
| T44/T45, sin equivalencia segura completa | `gobierno`, `EventoAuditoria`, middleware y señales. Políticas nuevas, versión única y aceptación obligatoria renovada; auditoría de metadatos consultable. No registra cuerpos, contraseñas, tokens ni texto clínico. |
| RF-06, UserProfileController | `perfil`: consulta y modificación de nombres, apellidos, teléfono, nacimiento y sexo propios. Campos institucionales de solo lectura; rol, permisos, email, código y área/cargo se gestionan por administración. |
| RF-07/08/16/17/18/42, CRUD Laravel | `/api/institucional/` y feature Admin: repositorio limitado a NUEVO_TRABAJADOR/TRABAJADOR/PSICOLOGO. Alta solo nuevo trabajador/psicólogo. Los IDs de ADMIN/SA no se exponen ni editan; no hay endpoint de cambio de rol. Catálogos, contenido y reasignación reutilizan casos probados. |
| RF-42, relación SASPEL existente | Configuración de cargos por área. PUT valida catálogo activo, duplicados y UUID; conserva relaciones mediante baja lógica y reactivación de la misma fila. No cambia perfiles históricos. |
| RF-02/03, cierre de sesión Laravel | `version_sesion` y verificación del hash de contraseña en JWT. Logout revoca todas las sesiones emitidas de la cuenta, incluso si el access expiró pero refresh sigue válido. Cambiar/restablecer contraseña invalida tokens anteriores. Primer acceso entrega tokens nuevos; respuestas tardías no restauran sesión cerrada. |

## API incorporada

Todos los caminos siguientes llevan prefijo `/api/`. Se exige JWT y cumplimiento
de primer acceso donde corresponde; GET es de consulta. Las vistas traducen
ausencia a 404, falta de permiso a 403 y validación a 400; credenciales inválidas
a 401. Las respuestas sensibles usan `Cache-Control: no-store`.

| Método y ruta | Acceso / cuerpo principal |
| --- | --- |
| POST `auth/logout/` | Refresh firmado de la cuenta; `{refresh}` → 204. |
| GET/PATCH `perfil/` | Usuario propio; lista permitida de campos personales. |
| GET/POST `psicologo/trabajadores/{id}/instrumentos/` | Psicólogo asignado o Superadmin; POST `{instrumento_id, fecha_limite?}`. |
| GET `trabajador/instrumentos/` | Trabajador propio. |
| GET `trabajador/evaluaciones/{asignacion}/` | Propietario de asignación no inicial. |
| POST `trabajador/evaluaciones/{asignacion}/{accion}/` | iniciar/respuestas/finalizar; contrato de respuestas existente. |
| POST `citas/{id}/reprogramar/` | Psicólogo asignado; fechas y motivo; devuelve sucesora. |
| GET/POST `seguimientos/{id}/recomendaciones/` | Profesional asignado; POST `{texto}`. |
| POST `seguimientos/{id}/recomendaciones/{id}/estado/` | `{estado}` válido; no permite falsificar autor. |
| GET `trabajador/evolucion/` | Propia; desde/hasta/instrumento_id opcionales. |
| GET `psicologo/trabajadores/{id}/evolucion/` | Asignación vigente; mismos filtros. |
| GET/POST `administracion/politicas/` | Solo Superadmin; nueva versión, nunca modificación retrospectiva. |
| GET `administracion/auditoria/` | SA: metadatos globales; ADMIN: operaciones propias en entidades administrativas permitidas. Paginación de 50 y filtros. |
| `institucional/…` | Contratos de users, areas, cargos, instruments, scales y assignments equivalentes a Superadmin con ámbito acotado. Excluye users/{id}/role/. |
| GET/PUT `{superadmin|institucional}/areas/{id}/cargos/` | Administración; `{cargo_ids: UUID[]}`. Lista vacía desvincula para nuevos usos, conserva perfiles. |

Las fuentes canónicas de serializers y rutas están en
`backend/src/infrastructure/api/rest/`; los contratos TypeScript se encuentran
junto a cada feature. No se cambió el contrato de las rutas originales
`/superadmin/` para permitir ADMIN.

## Modelo, normalización y migraciones

Se conserva la cadena relacional existente: Usuario → PerfilUsuario (uno a uno),
área y cargo por FK, catálogo AreaCargo con par único; AsignacionProfesional
vincula trabajador y psicólogo; Instrumento → Pregunta → Escala → Opcion;
AsignacionInstrumento → Aplicacion → Respuesta/Resultado; Cita → Nota;
Seguimiento → Recomendacion; Resultado → Alerta → AccionAlerta;
PoliticaSistema → AceptacionPolitica. Las entidades tienen UUID y relaciones
PROTECT cuando la eliminación rompería historial.

Las nuevas recomendaciones dependen de su identificador, seguimiento y autor:
no duplican nombres, trabajadores ni contenido del seguimiento. Auditoría guarda
una referencia polimórfica UUID más nombre de entidad: es una excepción técnica
de trazabilidad y no una FK a cada tabla; no se usa como fuente de datos de
negocio. El resultado numérico persistido es una instantánea calculada para
trazabilidad; no se recalcula en consultas. Estas dos decisiones se documentan
como materialización técnica, no duplicación de catálogos. La inspección de
modelos/constraints respalda el diseño 3FN; no sustituye una demostración formal
de todas las dependencias funcionales del sistema.

| Migración | Cambio aditivo | Reversión |
| --- | --- | --- |
| 0013_recomendaciones | Tabla con FK seguimiento/profesional, texto, estado restringido, auditoría base e índice. | Quita tabla; perdería recomendaciones nuevas. Solo se ensayó en BD sintética. |
| 0014_auditoria_funcional | Tabla de eventos, actor nullable PROTECT, fecha/acción/entidad/UUID/estado e índice. | Quita eventos; no ejecutar sobre historial real sin estrategia de conservación. |
| 0015_revocacion_sesion | Entero `Usuario.version_sesion`, valor inicial 0. | Quita contador; exige invalidar JWT emitidos antes de retroceder versión. |

Se verificó instalación limpia, reversión 0015→0012 y reaplicación en clúster
efímero. `makemigrations --check --dry-run` no detectó diferencias. En la base
local configurada se creó primero `.cache/completar/respaldo-local/antes-0013-0015.dump`,
se verificó su catálogo y se aplicaron las tres migraciones. Se compararon los
conteos de las tablas SASPEL preexistentes antes/después: se conservaron. El dump
es local, privado y está ignorado por Git; no se incorpora a evidencia pública.

## Concurrencia y límites operativos

Se conserva el bloqueo compartido de administración en Group SUPERADMIN para
operaciones que deben excluir reasignaciones, cambios de rol y reservas de agenda.
La resolución bloquea asignación, instrumento y escalas; las ediciones de contenido
usan sus bloqueos de padre. No se afirma que esto sea una solución de alto
rendimiento: hace falta carga representativa para dimensionar el despliegue.

La revocación remota exige que la petición de logout alcance la API. Sin red,
el navegador elimina sus tokens, pero la revocación en servidor no puede
garantizarse hasta reconectar o expirar. Los JWT se mantienen en el mecanismo
de almacenamiento existente; no se migró la arquitectura a cookies HttpOnly.

EventoAuditoria bloquea save/delete de instancias existentes y la API no expone
edición. Un administrador de BD o un QuerySet/SQL directo puede eludirlo; no es
almacenamiento WORM ni firma criptográfica. No se auditan GET, cuerpos ni lecturas
de documentos. No se añadieron textos legales, reglas clínicas o umbrales nuevos
sin aprobación.
