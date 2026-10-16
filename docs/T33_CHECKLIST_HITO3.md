# T33 · Validación del alcance y checklist Hito 3

Revisión final del conjunto con Fecha Fin ≤ 19/10/2026, ejecutada el 16/10/2026. Fuente de alcance: Cronograma de SASPELCronograma3.xlsx. Código conjunto validado en cb2758c; esta entrega añade únicamente el checklist. No declara terminadas las tareas posteriores al corte ni sustituye la presentación final T43.

## Resultado del corte inicial al 19/10/2026

37 tareas objetivo: 25 ya completas antes de esta ejecución; 12 incompletas revisadas. Se cerraron T14, T16, T29, T31, T32, T34, T35, T36 y T37; T33 queda lista para cierre al integrar/publicar este checklist. Resultado tras esa integración: 35 Completado, 2 En curso. Actualización del 16/10/2026: el responsable del desarrollo aprobó expresamente el modelo T13, cuyo criterio no exige terceros. Con su cierre, el corte quedó en 36 Completado, 1 En curso. Posteriormente, el responsable autorizó el criterio de reconstrucción lógica de T08, acreditado en [T16](T16_PAQUETE_HITO2.md#t08--línea-base-lógica-y-límites-de-la-evidencia). Con T08 Completado, el corte queda en **37 Completado de 37**, ninguna En curso ni Pendiente.

| Tarea o grupo | Evidencia revisada |
| --- | --- |
| T01–T07 | Arranque y configuración existente; tests health, auth y arquitectura; PostgreSQL operativo. |
| T08 | Línea base lógica reconstruida con README, migraciones originales e historial Git; criterio documental autorizado satisfecho. Completado. Esquema físico anterior no verificable. |
| T09–T12 | Inventario, alcance, roles y reglas de las hojas funcionales del cronograma. |
| T13 | [Modelo conceptual](T13_MODELO_DOMINIO.md) terminado, revisado y aprobado por el responsable del desarrollo el 16/10/2026. Completado. |
| T14 | [DER y diccionario](T14_DER_DICCIONARIO.md), 24 entidades y auditoría UUID comprobada. |
| T15–T16 | Mapa de casos de uso/puertos y [paquete de revisión Hito 2](T16_PAQUETE_HITO2.md). |
| T17–T18 | Modelos y migraciones; tests de esquema inicial, instrumentos, citas y UUID. |
| T19–T22 | Acceso JWT, primer acceso, guards, MVVM y administración de usuarios; suites backend/frontend. |
| T23 | Asignaciones, historial y concurrencia; tests de asignaciones. |
| T24–T28 | Configuración de instrumentos, respuestas, cálculo persistido y flujo de aplicación; suites de instrumentos y cierre de onboarding. |
| T29 | Resultados/historial autorizado; feature existente 962698d integrada y publicada. |
| T30–T31 | Modelos de agenda y flujo de solicitud, aceptación/rechazo, consulta y cancelación; confirmaciones concurrentes sin doble reserva. |
| T32 | [Informe pre-H3](T32_INTEGRACION_NUCLEO.md) y recorrido integrado con JWT y PostgreSQL temporal. |
| T33 | Este checklist, backlog priorizado y bloqueos separados de la integración funcional. |
| T34 | Notas privadas asociadas a citas realizadas, con autor y fecha; acceso restringido al profesional autorizado. |
| T35 | Seguimiento cronológico, estado, evolución, observación, plan y próxima revisión opcional. |
| T36 | Ánimo propio y consulta por profesional con asignación activa. |
| T37 | Tipos de factores configurables y registros propios cronológicos; nombre histórico preservado. |

## Checklist ejecutado

- [x] Dependencias núcleo T21, T29 y T31 integradas antes de validar T32.
- [x] Login → evaluación inicial → resultado → transición de rol → asignación profesional → cita → cancelación funciona en prueba integrada HTTP, sin mocks de negocio.
- [x] Revocar la asignación corta el acceso profesional a resultados, citas y datos de seguimiento/bienestar.
- [x] Notas y seguimiento rechazan acceso de trabajador, otro profesional y administración; bienestar conserva propiedad del trabajador.
- [x] Campos de propietario, autor y fecha no se aceptan como sustituciones del actor y la fecha del servidor.
- [x] Cambios de estado conservan historial; no se exponen operaciones de borrado físico para los registros nuevos.
- [x] Confirmaciones concurrentes impiden citas solapadas; intervalos adyacentes son válidos.
- [x] Estados de carga, errores, vacío, guardado y formularios se verificaron mediante pruebas de componentes.
- [x] Suite backend completa: **371 descubiertas, 370 aprobadas, 1 omitida**, 26,502 s. Comando: `python manage.py test tests --noinput --verbosity 1` desde backend con el entorno del proyecto.
- [x] Suite frontend completa: **192/192**, 17 archivos. Comando: `npm test -- --watch=false`.
- [x] Build Angular de producción aprobado: `npm run build`.
- [x] `manage.py check`, `migrate --check` y `makemigrations --check --dry-run`: sin errores ni migraciones pendientes.
- [x] SASPEL2 conserva todos los registros preexistentes: comparación de conteos y SHA-256 sobre hashes de filas en transacciones de solo lectura. Solo se añaden cinco tablas y los metadatos Django de las migraciones; las cinco tablas nuevas están vacías, sin semillas ficticias.
- [x] Backup SASPEL2C.sql idéntico por SHA-256; no ejecutado, restaurado, importado ni copiado al proyecto.
- [x] Excel conserva las 47 partes originales del paquete; solo difieren valores de Estado en Cronograma y, por autorización posterior, el criterio de T08 en G9. El cierre de T08 modifica únicamente G9 y L9. No se cambian las otras hojas, fórmulas, fechas, estilos, filtros o estructura, ni se versiona el archivo.
- [x] main local y origin/main conservan e83502fb7b067a8cec9e05e463f6d8120155a7b2. Las features se publican e integran secuencialmente en develop, sin force push ni borrado de historia.

La prueba omitida es UnifiedUsersBrowserTests, optativa y dependiente de Angular/Playwright activos. Las 192 pruebas frontend usan el entorno de componentes y HTTP simulado; no se presentan como una aprobación E2E en navegador ni como aceptación de usuarios. T55 cubre la validación E2E integral posterior.

## Bloqueos y condiciones de cierre

| ID | Evidencia / pendiente concreto | Impacto | Condición de cierre |
| --- | --- | --- | --- |
| T08 | Reconstrucción lógica documentada en T16; backup de 28 tablas solo complementario. El esquema físico anterior no es verificable. | Reserva documental resuelta; limitación histórica conservada. | Nuevo criterio autorizado satisfecho mediante README, migraciones e historial Git. No se inventa un dump histórico. |


No hay bloqueador técnico global identificado dentro de los escenarios ejecutados. T08 queda Completado conforme al criterio documental autorizado. El pendiente de aprobación de T13 quedó resuelto por la declaración explícita del responsable del desarrollo, registrada en el modelo conceptual; no se atribuye aprobación a terceros. El catálogo de factores queda deliberadamente vacío hasta que Administración configure los tipos reales de la institución; la función de configuración está implementada y probada con datos temporales, sin inventar tipos de negocio.

## Backlog registrado al corte inicial del 19/10/2026

| Orden | Tarea | Fecha Fin | Prioridad del Excel | Dependencias y siguiente resultado exigido |
| --- | --- | --- | --- | --- |
| 1 | T38 · Alertas por reglas explícitas | 20/10/2026 | Alta | T27/T35/T36 disponibles. Antes de codificar, identificar las condiciones de negocio concretas; no deducir umbrales clínicos ni incorporar ML. |
| 2 | T39 · Notificaciones internas | 21/10/2026 | Media | T31 disponible; requiere T38. Eventos dirigidos a usuarios, consulta y estado de lectura. |
| 3 | T40 · Dashboards por rol | 22/10/2026 | Media | T29/T31/T35 disponibles. Completar indicadores operativos derivados de datos reales; los accesos existentes no equivalen a todos los indicadores terminados. |
| 4 | T41 · Reportes operativos | 23/10/2026 | Media | T29/T35 disponibles. Definir los listados/exportables y filtros previstos respetando permisos. |
| 5 | T42 · Pruebas funcionales H3 | 23/10/2026 | Alta | T35 disponible, T38/T41 pendientes. Cerrar defectos de severidad alta del conjunto ampliado. |
| 6 | T43 · Preparar y presentar H3 | 24/10/2026 | Alta | Requiere T42. Demo estable, datos de prueba y evidencia, con congelación de versión de demostración. |

El orden respeta dependencias y fechas. Las prioridades altas de T42/T43 no permiten ejecutarlas antes de disponer del alcance que deben validar. T44 en adelante, recomendaciones T48 y evolución histórica ampliada permanecen fuera de esta ejecución. Ninguna tarea posterior al 19/10 se cambia de estado.

## Trazabilidad de integración de esta ejecución

| Tarea | Commit de implementación/entregable |
| --- | --- |
| T29 | 962698d |
| T31 | 6cadd1a |
| T32 | e8a55ae |
| T34 | c59b3ea |
| T35 | 8a7792f |
| T36 | 1bffe8c |
| T37 | fbdfc56 |
| T13, diseño original; aprobación posterior documentada en el modelo | 1e32168 |
| T14 | 843ce60 |
| T16 | cb2758c |

Cada commit fue publicado en su feature y posteriormente en develop. El cierre de T33 requiere publicar este documento en develop y después cambiar únicamente su Estado en el Excel local. Los únicos archivos locales no versionados esperados son el cronograma y su archivo temporal de bloqueo de Excel.

## T42 · Validación integrada del Hito 3 hasta 24/10/2026

Verificación del 16/10/2026 tras integrar T38–T41 en develop. Este apartado actualiza el backlog histórico anterior y amplía el corte de 37 a 43 tareas. El cronograma es local y no se versiona. No se declara una aceptación o presentación externa.

| Tarea | Criterio literal | Evidencia integrada |
| --- | --- | --- |
| T38 | Alertas se generan por condiciones de negocio definidas y quedan trazables. | e53c154: regla selecciona RangoInterpretacion existente y nivel de atención; evento de resultado finalizado genera una alerta única por regla/resultado; acciones con autor, fecha y estado. Sin umbrales médicos ni semillas. |
| T39 | Eventos relevantes generan notificaciones consultables y marcables como leídas. | 86902ba y 7c08829: citas, asignaciones, instrumentos, resultados, alertas y asignación pendiente. Destinatario individual, lectura idempotente, resumen sin contenido clínico y revocación del acceso profesional. |
| T40 | Cada rol ve indicadores operativos derivados de datos reales del sistema. | 67733c1: indicadores para Trabajador, Psicólogo, Admin y Superadmin; Nuevo Trabajador conserva onboarding. Conteos autorizados en backend y estados de carga, vacío y error. |
| T41 | Listados y exportables definidos por negocio funcionan con filtros principales. | c5285a9: usuarios, instrumentos, citas y seguimiento (RF-44). Fechas, estado y área/instrumento según reporte; páginas de 50 filas y CSV con igual autorización/filtros, hasta 10000 filas. El criterio no fija formato: CSV es el único formato implementado. |
| T42 | Escenarios críticos pasan y defectos de severidad alta quedan cerrados. | Suite completa y recorrido HTTP integrado descritos a continuación, sin defectos de severidad alta identificados en los escenarios ejecutados. |

Dependencias verificadas en el Excel: T38 requiere T27/T35/T36; T39 requiere T31/T38; T40 requiere T29/T31/T35; T41 requiere T29/T35; T42 requiere T35/T38/T41. Todas están Completadas e integradas antes del cierre de T42.

### Escenarios y resultados

- Backend: `python backend/manage.py test tests --noinput --verbosity 1` con el Python del entorno local. **392 descubiertas, 391 aprobadas y 1 omitida**, 32,396 s. Incluye login/primer acceso/roles, evaluación inicial, resultados e historial, asignación, citas, notas, seguimiento, ánimo y factores, reglas/acciones de alertas, notificaciones, dashboards, reportes y accesos cruzados negativos.
- `tests.test_integracion_hito3` usa HTTP, JWT y PostgreSQL temporal: configuración administrativa de regla sobre un rango de prueba existente → login Nuevo Trabajador → evaluación/respuestas → resultado → cambio de rol → asignación profesional → alerta y notificación → cita confirmada/completada → nota y seguimiento → ánimo y factor → dashboards/reportes/CSV → revocación. Solo se controla el reloj para finalizar la cita; no se simulan servicios de negocio ni persistencia.
- Frontend: `npm test -- --watch=false`, **200/200 aprobadas en 20 archivos**, 5,78 s. La primera corrida falló por nuevas peticiones /api/dashboard/ sin respuesta en fixtures antiguos de navegación; se añadieron respuestas explícitas a esos escenarios, conservando todas las aserciones y la comprobación de peticiones pendientes. No se deshabilitaron pruebas.
- Angular: `npm run build` aprobado después de la suite frontend. No equivale a una prueba E2E de navegador.
- Django: `check`, `migrate --check` y `makemigrations --check --dry-run` aprobados, sin migraciones pendientes ni cambios detectados.
- UUID/auditoría: la prueba registra y verifica las **28 entidades** actuales, incluidas ReglaAlerta, Alerta, AccionAlerta y Notificacion; conserva las claves UUID, relaciones y campos de AuditableModel.

La prueba omitida sigue siendo `UnifiedUsersBrowserTests`, optativa y habilitada solo con `SASPEL_BROWSER_TEST=1`; requiere Angular y Playwright. Se registra como omitida, no aprobada. La validación E2E integral T55 queda fuera de este corte.

### Conservación de datos y límites

Migraciones 0011_alertas_reglas y 0012_notificaciones_internas aplicadas sin restaurar ni resetear SASPEL2. Añaden cuatro tablas, todas vacías al verificar. Se compararon conteos y huellas SHA-256 de las filas de las 33 tablas anteriores: datos de negocio sin cambios. En auth_permission, django_content_type y django_migrations se añadieron únicamente metadatos de estas migraciones; excluyendo esas altas, las huellas de todos sus registros anteriores coinciden. El backup mantiene SHA-256 `a96349eb27d5c33823cdb51922f54ce5c566566647e788e3144bfca8b2a787a1`.

No se habilitan reglas clínicas por defecto ni se llenan pantallas con registros ficticios. La institución debe configurar rangos y reglas según su proceso. Los reportes administrativos de citas y seguimiento son agregados y no exponen notas, observaciones, evolución, factores, ánimo o resultados individuales. El profesional pierde acceso a alertas, notificaciones vinculadas, reportes y registros sensibles tras perder la asignación vigente.
