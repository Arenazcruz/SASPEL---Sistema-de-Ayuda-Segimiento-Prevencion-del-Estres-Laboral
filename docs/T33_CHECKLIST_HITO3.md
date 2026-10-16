# T33 · Validación del alcance y checklist Hito 3

Revisión final del conjunto con Fecha Fin ≤ 19/10/2026, ejecutada el 16/10/2026. Fuente de alcance: Cronograma de SASPELCronograma3.xlsx. Código conjunto validado en cb2758c; esta entrega añade únicamente el checklist. No declara terminadas las tareas posteriores al corte ni sustituye la presentación final T43.

## Resultado del corte

37 tareas objetivo: 25 ya completas antes de esta ejecución; 12 incompletas revisadas. Se cerraron T14, T16, T29, T31, T32, T34, T35, T36 y T37; T33 queda lista para cierre al integrar/publicar este checklist. Resultado previsto tras esa integración: **35 Completado, 2 En curso**, ninguna Pendiente dentro del corte.

| Tarea o grupo | Evidencia revisada |
| --- | --- |
| T01–T07 | Arranque y configuración existente; tests health, auth y arquitectura; PostgreSQL operativo. |
| T08 | Dump autorizado inspeccionado en lectura; evidencia histórica insuficiente. En curso. |
| T09–T12 | Inventario, alcance, roles y reglas de las hojas funcionales del cronograma. |
| T13 | [Modelo conceptual](T13_MODELO_DOMINIO.md) terminado y revisado; aprobación funcional no acreditada. En curso. |
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
- [x] Excel conserva las 47 partes originales del paquete; solo difieren valores de Estado en Cronograma. No se cambian las otras hojas, fórmulas, fechas, estilos, filtros o estructura, ni se versiona el archivo.
- [x] main local y origin/main conservan e83502fb7b067a8cec9e05e463f6d8120155a7b2. Las features se publican e integran secuencialmente en develop, sin force push ni borrado de historia.

La prueba omitida es UnifiedUsersBrowserTests, optativa y dependiente de Angular/Playwright activos. Las 192 pruebas frontend usan el entorno de componentes y HTTP simulado; no se presentan como una aprobación E2E en navegador ni como aceptación de usuarios. T55 cubre la validación E2E integral posterior.

## Bloqueos y condiciones de cierre

| ID | Evidencia / pendiente concreto | Impacto | Condición de cierre |
| --- | --- | --- | --- |
| T08 | SASPEL2C.sql tiene 28 CREATE TABLE, incluidas tablas de negocio. No acredita la etapa histórica de solo tablas técnicas Django. | Documental; no bloquea los módulos integrados. | Evidencia histórica compatible con el criterio original, o cambio explícitamente autorizado de ese criterio. No se sustituye por el esquema actual. |
| T13 | Modelo conceptual entregado y revisado, sin constancia de aprobación funcional por el responsable. | Aceptación del entregable; el diseño permite continuar la revisión técnica. | Aprobación del modelo entregado o indicación explícita de la evidencia válida. No se atribuye aprobación al usuario. |

No hay bloqueador técnico global identificado dentro de los escenarios ejecutados. T08/T13 conservan En curso. El catálogo de factores queda deliberadamente vacío hasta que Administración configure los tipos reales de la institución; la función de configuración está implementada y probada con datos temporales, sin inventar tipos de negocio.

## Backlog restante H3, priorizado sin adelantar implementación

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
| T13, entregable sin aprobación | 1e32168 |
| T14 | 843ce60 |
| T16 | cb2758c |

Cada commit fue publicado en su feature y posteriormente en develop. El cierre de T33 requiere publicar este documento en develop y después cambiar únicamente su Estado en el Excel local. Los únicos archivos locales no versionados esperados son el cronograma y su archivo temporal de bloqueo de Excel.
