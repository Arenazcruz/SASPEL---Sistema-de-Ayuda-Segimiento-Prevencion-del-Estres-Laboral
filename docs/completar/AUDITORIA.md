# Auditoría comparativa SASPE-UF → SASPEL

Fecha: 26/10/2026. Véanse [matriz de requisitos](MATRIZ.md), [plan](PLAN.md),
[implementación](IMPLEMENTACION.md), [pruebas](PRUEBAS.md) e [informe](INFORME.md).

## Alcance y método

Se verificaron las rutas de ambos proyectos, el Excel y origin del repositorio.
SASPE-UF se trató exclusivamente como fuente de consulta: no se ejecutó PHP,
Artisan, Composer, migraciones ni operaciones sobre su base de datos. Se recorrieron
rutas, controladores, FormRequests, modelos, servicios, configuración, vistas y
pruebas. [inventario.json](inventario.json) enumera archivos, hashes, líneas,
símbolos, tablas y relaciones detectadas; [inventariar.py](inventariar.py) permite
reproducirlo. Un inventario no demuestra ejecución ni revisión semántica de cada
línea. Los hallazgos siguientes distinguen el análisis estático de las pruebas
efectivamente ejecutadas en SASPEL.

Se leyeron las 12 hojas del cronograma mediante openpyxl, sin guardarlo:
Resumen, Cronograma, Gantt, Alcance, ReqFuncionales, ReqNoFuncionales,
RolesPermisos, ReglasNegocio, HistoriasUsuario, ProductoBacklog, SprintsHitos y
CasosUso. Sus estados no son uniformes: ReqFuncionales conserva «Pendiente» en
RF-01–49, mientras Cronograma registra numerosos desarrollos concluidos. La
clasificación de este informe depende del código y de sus pruebas, no de esos
estados. No se modificaron el Excel ni documentos académicos.

La aclaración expresa del usuario establece **una sola institución**. Se resuelve
así el alcance de ADMIN sin crear un modelo multiinstitución ni concederle acceso
a cuentas administrativas globales o contenido psicológico privado.

## Referencia Laravel: estructura y hallazgos

`composer.json` declara PHP ^8.2, Laravel ^12 y laravel-dompdf ^3.1. La presentación
usa Blade/Vite. `routes/web.php` contiene rutas de controladores y `Route::view`;
varias vistas consultan directamente la base. La lógica se reparte entre
controladores, modelos y `app/Services/InstrumentService.php`. No corresponde
trasladar esta distribución al núcleo hexagonal actual.

Las ubicaciones siguientes son relativas a `C:\laragon\www\Original\SASPE-UF`.

| Módulo y ubicación | Implementación observada | Decisión SASPEL |
| --- | --- | --- |
| `app/Http/Controllers/auth/ManualLoginController.php` | Hash y fallback de comparación de contraseña heredada en texto; regeneración de sesión y cierre. | Conservar Django Auth/JWT; excluir el fallback inseguro; añadir revocación real. |
| `routes/web.php`, `bootstrap/app.php` | Muchas rutas protegidas solo por autenticación, sin middleware de rol equivalente en bootstrap. | Roles actuales y permisos de objeto en servidor; los guards Angular no sustituyen autorización. |
| `AdminStudentRegistrationController.php`, `AdminStudentManagementController.php` | CRUD de estudiantes, validación propia y campo tamizaje en entrada. No equivale a trabajadores ni a onboarding autorizado. | Personal institucional, código empleado, validaciones vigentes 19–77 años; transición de rol solo al finalizar evaluación. |
| `AdminPsychologistRegistrationController.php`, `AdminPsychologistManagementController.php`, `Superadmin/GestionAdminController.php` | Gestión separada por categoría. | Reutilizar CRUD unificado SASPEL con repositorio limitado para ADMIN. |
| `UserProfileController.php` | Actualización de campos propios; aviso de cambio difundido a profesionales y administradores. | Lista permitida de campos personales; sin difusión general. Área/cargo y rol son administrativos. |
| `InstrumentTestController.php`, `app/Services/InstrumentService.php` | Validación de opciones, aplicaciones/respuestas, suma, subescalas y rangos configurados; sincronización de preguntas y catálogo por slug. | Mantener motor genérico actual y Decimal; asignación explícita, preguntas ordenadas y versiones utilizadas protegidas. No copiar umbrales académicos. |
| `InstrumentService.php` | Selección del profesional por carga; no reproduce todas las garantías actuales de empate, elegibilidad y exclusión concurrente. | Conservar asignación automática probada, menor carga, mayor antigüedad desde última asignación y bloqueo. |
| `Psychology/AssignTestController.php` | Comprueba relación profesional, instrumentos permitidos y pendientes; admite fecha límite. | Adaptar al catálogo UUID, actor autenticado y ausencia de duplicado pendiente bajo transacción. |
| `Tools/AssignedTestsController.php` | Listado propio por vínculo; rutas fijas y condición `locked` dependiente de plazo para completados. | Ruta genérica, estado persistido; finalizadas nunca editables aunque venza un plazo. |
| `Psychology/AppointmentController.php` | Agenda y comprobación de cruce; catálogo amplio de estudiantes; edición cambia horario original. No se observa bloqueo concurrente equivalente. | Mantener disponibilidad y autorización por asignación; reprogramar crea sucesora y conserva original. |
| `Psychology/ReviewTestController.php`, `Psychology/StudentResultController.php` | El listado limita por asignación, pero la consulta directa de resultado por estudiante no reproduce esa comprobación en el método inspeccionado. Riesgo de acceso por identificador según ruta autenticada. | Revalidar asignación activa en cada consulta de resultado, evolución, nota y seguimiento. Hallazgo estático, no explotación ejecutada. |
| `TestResultController.php`, `TestHistoryController.php` | Consulta propia e historial; exportación PDF y HTML con extensión XLS. | Preservar consulta segura y reportes CSV actuales; no existe requisito de copiar formatos de Laravel. |
| `TestProfesionalController.php`, FormRequests `Store*Request.php`, modelos `TestProfesionalSesion`, `ResumenTestProfesional`, `HistoriaClinicaBreve` | Sesiones/formularios profesionales con información clínica y variables académicas. | Seguimiento laboral explícito, autor y fecha; recomendaciones manuales vinculadas. No migrar historias clínicas reales. |
| `MoodRecordController.php` | Nivel 1–5, intervalo de dos horas, diferencia exactamente uno; contiene DDL para quitar una restricción durante una petición. | Conservar reglas SASPEL; excluir DDL en peticiones y restricciones no aprobadas. |
| `app/Models/Notificacion.php` y controladores de notificaciones | El evento de creación redistribuye contenido a administradores. | Notificaciones dirigidas y genéricas; sin puntajes, respuestas o textos privados en difusión administrativa. |
| `resources/views` (evolución/historial) | Gráficos, categorías heurísticas y lógica de transición tipo Markov. | Solo series históricas por instrumento/versión; diferencia descriptiva, sin predicción ni diagnóstico. |
| `ChatController`, modelos `Chat*`; `Diary*Controller`, modelos `Diario*` | Chat y diario tienen código propio. | DESCARTADO del alcance vigente; evolución no reintroduce chat ni diario. |

Los nombres cortos de controladores de la tabla se encuentran en
`app/Http/Controllers/`. El inventario incluye sus rutas exactas y símbolos.

### Datos, código incompleto y límites de la referencia

Los modelos permiten reconstruir conceptualmente usuario → asignación → aplicación
→ respuesta/resultado, citas/notas y sesiones profesionales. Sin embargo, no se
encontraron migraciones en `database/migrations`. No se abrió la base SQLite ni
se consultó una base externa. El esquema físico, restricciones desplegadas, datos,
integridad y funcionamiento real de Laravel quedan **NO VERIFICADOS**. No se
deduce una FK física solo de un `belongsTo`.

Las dos pruebas de ejemplo (verdadero unitario y página inicial) no demuestran
los flujos psicológicos ni la seguridad de roles. No se ejecutaron. Las consultas
en Blade y las rutas directas impiden declarar código «muerto» solo por ausencia
de llamadas desde controladores. Los archivos sin referencia detectada son
candidatos a revisión, no se eliminaron ni se usaron como prueba funcional.

## SASPEL al inicio

Base: Django 6.1 / DRF 3.18 / Angular 21 / PostgreSQL, usuario UUID, borrado lógico,
migraciones hasta 0012, capas Domain/Application/Infrastructure y frontend por
funcionalidades. La suite inicial descubrió 428 pruebas backend (427 aprobadas,
una de navegador omitida por configuración) y 209 pruebas frontend aprobadas.

Ya funcionaban autenticación institucional, primer acceso, aceptación de políticas,
onboarding, resolución inicial y cambio de rol, asignación profesional con desempate,
CRUD Superadmin, instrumentos y contenido, resultados, citas/disponibilidad,
notas privadas, ánimo, factores, seguimiento, alertas explícitas, notificaciones,
indicadores y reportes. Existían garantías de permisos de objeto, transacciones,
constraints y exportación CSV protegida frente a fórmulas. Se conservaron.

Faltaban o estaban parciales: revocación de JWT al cerrar/cambiar contraseña,
perfil propio posterior al onboarding, gestión efectiva de ADMIN, vínculo
área–cargo editable, reprogramación con historia, asignación/resolución profesional
posterior al onboarding, recomendaciones, evolución comparable, auditoría
consultable y publicación de nuevas políticas. Había tablas y rutas de funciones
relacionadas, pero su existencia por sí sola no cerraba esos flujos.

El estado de Git inicial estaba limpio en archivos versionados. Se conservaron
sin incorporar los archivos locales de auditoría SQL, `docs/seguridad/` y `gestion/`.
Se creó `codex/completar-saspel-referencia` desde la rama existente
`feature/auditoria-validaciones-pre-h4`; no hubo reset, limpieza general, push ni merge.

## Seguridad comprobada y límites

Las pruebas cubren autenticación, rol actual, UUID ajeno, trabajador ajeno,
profesional reasignado, campos desconocidos, datos inválidos, duplicados,
transiciones, filtros, SQL parametrizado y concurrencia. Los tests locales
preexistentes de auditoría SQL se ejecutaron sin modificarlos. Las capas de dominio
y aplicación siguen sin imports Django/DRF, comprobado con AST.

Angular interpola texto; no se añade HTML confiable procedente del usuario.
La API usa Bearer explícito y no cookies de sesión para estas operaciones; Django
mantiene CSRF para su administración por sesión. CORS y DEBUG deben configurarse
para el despliegue real. No se certifica resistencia universal a XSS/SQLi ni
cumplimiento jurídico a partir de pruebas funcionales.

Las consultas GET no generan escrituras de auditoría. El registro cubre cambios
de modelos y mutaciones API exitosas; no es un registro de todas las lecturas ni
un almacén inviolable frente a un administrador de PostgreSQL. Las operaciones
ORM masivas/SQL fuera de los casos autorizados no quedan cubiertas por post_save.
El bloqueo compartido existente simplifica consistencia, pero requiere medición
de carga antes de afirmar capacidad institucional a gran escala.
