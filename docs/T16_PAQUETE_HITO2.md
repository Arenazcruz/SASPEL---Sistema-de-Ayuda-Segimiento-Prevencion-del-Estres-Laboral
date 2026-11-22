# T16 · Paquete de revisión Hito 2

Revisión realizada el 16/10/2026 sobre el estado integrado del proyecto. Es una entrega técnica actualizada, no un acta de aprobación histórica ni una certificación de aceptación institucional.

## Material de la entrega

| Componente | Entregable / fuente | Resultado de revisión |
| --- | --- | --- |
| Alcance | Cronograma local, hojas Alcance, ReqFuncionales, RolesPermisos y ReglasNegocio | Lógica de negocio SASPEL; cinco roles existentes; sin IA, chat ni ampliación del alcance. Corte de esta ejecución: T01–T37. |
| Dominio | [Modelo conceptual T13](T13_MODELO_DOMINIO.md) | Entidades, objetos de valor, invariantes y puertos documentados sin dependencia del ORM. Aprobación del responsable del desarrollo registrada en T13 el 16/10/2026. |
| Modelo lógico | [DER y diccionario T14](T14_DER_DICCIONARIO.md) | 24 entidades propias, 135 atributos específicos y auditoría común; revisión contra reglas, relaciones y restricciones. |
| Casos de uso | Hoja CasosUso del Excel y mapa incluido en T13 | Entradas, salidas y puertos principales definidos; no se confunden casos futuros con implementación disponible. |
| Arquitectura | [Guía de código](GUIA_CODIGO.md), backend/src y frontend/src/app | Backend hexagonal y frontend MVVM por features; tests de arquitectura protegen los límites. |
| Persistencia | Migraciones 0001–0010, PostgreSQL SASPEL2 | Esquema actual reproducible con migraciones; nuevas tablas añadidas sin reset ni pérdida de registros existentes. |
| Integración | [Informe pre-H3 T32](T32_INTEGRACION_NUCLEO.md) | Recorrido HTTP con JWT y PostgreSQL temporal; alcance y límites de pruebas explícitos. |
| Cronograma | gestion/SASPELCronograma3.xlsx, archivo local no versionado | 37 tareas hasta 19/10/2026; estados actualizados tras publicar develop; excepción autorizada: nuevo criterio documental de T08. Se conservan fechas y dependencias. |

## Arquitectura revisada

Backend: las vistas DRF traducen solicitudes y errores, Application coordina casos y permisos, Domain expresa reglas y valores, y los adaptadores Django implementan los puertos. Domain no depende de Application, Django o HTTP; Application no depende de Infrastructure. Las pruebas de importación comprueban esa dirección.

Frontend: Core contiene identidad, guards e interceptor. Cada feature separa vista, ViewModel, modelos de datos y servicio HTTP. ViewModels manejan carga, errores, formulario y navegación. La autorización definitiva permanece en backend. Nuevo Trabajador conserva onboarding; Trabajador tiene resultados, citas y bienestar; Psicólogo tiene trabajadores autorizados, resultados, agenda, notas y seguimiento. Administración configura catálogos sin recibir contenido clínico por esa capacidad.

Concurrencia: los casos sensibles comparten la transacción de asignaciones. La comprobación de permisos y la operación se realizan bajo el mismo bloqueo. Las solicitudes de citas no reservan un horario; la confirmación vuelve a validar disponibilidad y solapamiento. La suite contiene confirmaciones concurrentes y pruebas de reasignación/revocación.

Persistencia: UUID y AuditableModel se mantienen en las entidades propias. Desactivaciones y cambios de estado conservan historial. Las migraciones 0007–0010 añaden cinco tablas: notas de cita, seguimiento, ánimo, tipos de factor y factores. El proceso Django añade sus tipos de contenido/permisos técnicos. Se compararon conteos y huellas de todos los registros preexistentes: conservados. La base de pruebas es temporal y separada de SASPEL2.

## Revisión del alcance y dependencias

El paquete incorpora la implementación real posterior a la fecha original del Hito 2 para que sea presentable y coherente con el código actual. No intenta retroceder el desarrollo ni reconstruir fechas de aprobación inexistentes.

- T08: Completado con el criterio documental autorizado y la reconstrucción lógica registrada a continuación. El esquema físico anterior sigue sin evidencia verificable.
- T13: modelo preparado, revisado y aprobado expresamente por el responsable del desarrollo del proyecto el 16/10/2026. Su criterio no exige aprobación de terceros; la evidencia se registra en el propio modelo conceptual.
- T14/T15: DER, diccionario y mapa de casos de uso están disponibles para revisión. Sus contratos corresponden a los módulos existentes.
- T33: checklist del Hito 3 se emitirá después de la validación conjunta final; este paquete no declara entregado todo el alcance futuro H3/H4.

No se introducen nuevas decisiones clínicas. Estado/intensidad de ánimo, nivel de factor y estado/evolución de seguimiento son descripciones. Los tipos de factores los configura la institución; no se inventó un catálogo de negocio ni se insertaron datos de demostración en SASPEL2.

## Comprobaciones de esta revisión

Arquitectura y modelos/auditoría: 98/98 pruebas aprobadas en T14; cobertura UUID extendida a las 24 entidades. Las comprobaciones postintegración de UUID y arquitectura también pasaron (12/12). No hay divergencia entre modelos y migraciones. El informe T32 documenta el conjunto núcleo y sus límites; la validación global al cierre se registra en T33.

La guía se actualizó para retirar afirmaciones obsoletas sobre servicios de dominio vacíos y funciones ya implementadas. No se cambian tecnologías, arquitectura ni alcance. Este paquete satisface la revisión y preparación de T16; T08 queda resuelta con el nuevo criterio documental autorizado y T13 mediante la aprobación documentada del responsable.

## T08 · Línea base lógica y límites de la evidencia

El responsable del proyecto autorizó sustituir el criterio original por: «Línea base lógica previa a api.0001_initial reconstruida y documentada mediante migraciones, README e historial Git, diferenciándola del estado físico histórico no verificable.» Esta autorización permite el cierre documental; no certifica un esquema físico histórico.

Fuentes verificables: commit raíz `e83502fb7b067a8cec9e05e463f6d8120155a7b2`, su `README.md`, `backend/config/settings.py` y las migraciones originales de `backend/src/infrastructure/persistence/django/migrations/`. El README conserva la fase previa sin modelos ni migraciones propias y describe después el primer bloque físico de cuatro tablas. La configuración utiliza auth, admin, contenttypes y sessions de Django, sin sustituir AUTH_USER_MODEL. Se consultan esas versiones con `git show e83502f:README.md` y `git show e83502f:backend/src/infrastructure/persistence/django/migrations/0001_initial.py`; la migración actual fue reescrita posteriormente en `ed190223f220b6f7d5c574ff651e050104984ada` y no representa la primera versión.

Secuencia lógica reconstruida: antes de `api.0001_initial` no hay tablas propias definidas por las migraciones SASPEL; las aplicaciones técnicas Django aportan autenticación, administración, tipos de contenido y sesiones, con `django_migrations` como registro técnico. La `0001_initial` original, inicial y dependiente del usuario Django, crea `saspel_area_institucional`, `saspel_cargo_institucional`, `saspel_perfil_usuario` y `saspel_asignacion_profesional`. `0002_crear_roles_iniciales` añade grupos, sin tablas; `0003_instrumentos_psicologicos` añade nueve tablas y `0004_citas_disponibilidad` añade dos. Esta secuencia describe el modelo de migraciones, no fechas ni ejecución física acreditadas.

El primer commit versionado ya incluye esas 15 tablas funcionales. El historial completo disponible no contiene un commit anterior ni evidencia verificable del esquema físico previo. El README y las migraciones permiten reconstruir la línea base lógica, pero no demostrar qué tablas existieron materialmente entonces. No se atribuye existencia a ningún dump histórico no disponible.

El backup `C:\Users\jgabr\OneDrive\Documentos\SASPEL2C.sql`, inspeccionado solo en lectura, contiene 28 CREATE TABLE, incluidas tablas de negocio. Es evidencia complementaria de un estado posterior, no de la línea base física inicial. SHA-256: `a96349eb27d5c33823cdb51922f54ce5c566566647e788e3144bfca8b2a787a1`. No se ejecuta ni restaura. Con estas fuentes y límites explícitos se satisface el nuevo criterio y T08 se registra como Completado.
