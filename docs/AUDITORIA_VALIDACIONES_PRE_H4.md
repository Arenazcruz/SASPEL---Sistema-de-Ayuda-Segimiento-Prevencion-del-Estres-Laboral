# Auditoría preventiva de validaciones · 16/10/2026

## Validaciones revisadas

Base: develop `1f96ea0`, alcance implementado T01–T43. Contraste con las hojas Cronograma, ReglasNegocio y RolesPermisos de SASPELCronograma3.xlsx; inspección de endpoints, casos, dominio, repositorios, modelos/migraciones, formularios y pruebas. No se implementan tareas H4 ni se cambia el Excel.

Validación final: `python backend/manage.py test tests --noinput --verbosity 1`: 404 descubiertas, 403 aprobadas, 1 omitida (navegador optativo), 29,653 s. `ng test --watch=false`: 209/209 en 21 archivos; `ng build`, `manage.py check`, `migrate --check` y `makemigrations --check --dry-run`: correctos. Antes se ejecutaron regresiones focalizadas. SHA-256 del Excel antes/después: `327ee7b9a0cfb7ff7947b51991d14f71bdc0b9d3cb63ea7c478a91e8e4a35bc7`.

| Módulos | Controles existentes revisados |
|---|---|
| Autenticación y primer acceso | Dominio exacto @saspel.com, credenciales, actividad, presupuesto de intentos, JWT/refresh/me, contraseña temporal, políticas vigentes/versionadas y aceptación explícita; guards de sesión, rol y primer acceso. |
| Usuarios, perfiles, áreas/cargos | Obligatorios, nombres, código, email generado/duplicados, edad, teléfono, UUID, AreaCargo activo, PATCH combinado, roles y protección del último Superadmin; combos dependientes y doble envío. |
| Asignaciones profesionales | Personas distintas, roles/actividad/habilitación, una ACTIVA por trabajador, cierre/reasignación con historial, menor carga, bloqueo compartido y unicidad. |
| Instrumentos, preguntas, escalas y rangos | Código/versión e inicial activo únicos, pertenencia al padre, tipo/escala/opción, orden/valor únicos, límites de enteros, mínimo ≤ máximo y actividad. |
| Evaluación, respuestas y resultados | Propiedad, tipo de respuesta, opciones activas/ajenas, duplicados, obligatorias, precisión numérica, cierre idempotente, inversión y cálculo backend, un resultado por aplicación, historial sin recalcular. Cero rangos produce resultado sin clasificación; varios coincidentes impiden finalizar. |
| Citas y notas | Horario futuro, inicio < fin, disponibilidad, solapamientos y adyacencia, asignación vigente, transiciones y concurrencia; notas solo del profesional autorizado sobre cita completada, autor de sesión y texto de 1–10000 caracteres. |
| Seguimiento, ánimo y factores | Propiedad/asignación, campos requeridos, longitudes, próxima revisión no pasada, tipo de factor vigente; administración sin acceso clínico, historial cronológico y autor del servidor. |
| Alertas y notificaciones | Reglas explícitas, unicidad regla/resultado y destinatario/evento, acción profesional autorizada, lectura propia idempotente, revocación de acceso y resúmenes sin contenido clínico. |
| Dashboards y reportes | Indicadores reales por rol; filtros de tipos/UUID/fechas/estado, inicio ≤ fin, paginación, CSV autorizado y escape de fórmulas; administración recibe agregados clínicos. |
| Transversal Angular/BD | Required, formatos y límites existentes, carga/vacío/error/éxito, bloqueo de envío y cancelación al cambiar de recurso; FK/PROTECT, OneToOne, UNIQUE/CHECK, índices, nulabilidad, activo/deleted. Domain/Application siguen sin imports Django/DRF; MVVM conservado. |

Máquinas de estado existentes (sin añadir transiciones):

| Recurso | Transiciones y protección |
|---|---|
| Asignación de instrumento / aplicación | PENDIENTE → EN_PROGRESO → COMPLETADA / INICIADA → FINALIZADA. Inicio y finalización admiten retry controlado; cierre impide editar/resucitar. CANCELADA/ANULADA no habilitan edición. |
| Asignación profesional | ACTIVA → FINALIZADA o REASIGNADA; reasignación crea otro vínculo en la misma transacción. No reabre cerradas. |
| Cita | SOLICITADA → CONFIRMADA/RECHAZADA/CANCELADA; CONFIRMADA → CANCELADA/COMPLETADA. Completar exige fin alcanzado; estados terminales no vuelven atrás. REPROGRAMADA existe en modelo, sin implementar T46. |
| Alerta | ABIERTA → EN_ATENCION/CERRADA; EN_ATENCION → EN_ATENCION/CERRADA; CERRADA terminal. |
| Notificación | Sin lectura → leída; repetir conserva la fecha, sin operación de deslectura. |
| Seguimiento | Entradas cronológicas; estado/evolución son texto profesional, no una máquina con catálogo cerrado. No hay edición del historial publicado. |
| Usuario | Activo ↔ inactivo con protección administrativa; NUEVO_TRABAJADOR → TRABAJADOR solo por cierre de evaluación. Borrado lógico no equivale a desactivación reversible. |

## Defectos encontrados

1. Cuenta con `deleted=True` podía iniciar sesión, renovar JWT y acceder con tokens anteriores.
2. Administración/catálogos/asignación manual omitían filtros de borrado lógico en consultas o escrituras; una cuenta borrada contaba para proteger el último Superadmin.
3. Empate de carga se resolvía por correo antes de aplicar la antigüedad de la última asignación exigida por RN-ASG-04.
4. Páginas desmesuradas llegaban a OFFSET de PostgreSQL y provocaban error de servidor.
5. Administrador de bootstrap sin perfil recibía 403 en operaciones administrativas válidas; tampoco aparecía en ciertos conteos/listados.
6. Mensajes mostraban objetos/metadatos internos, errores vacíos o detalle de respuestas 500; duplicados de contenido exponían la clave interna `__all__`.
7. Citas liberaba `busy` al finalizar el POST mientras seguía pendiente la recarga, habilitando nuevas acciones antes de terminarla.

## Defectos corregidos

Los siete grupos anteriores quedan corregidos con regresiones en `backend/tests/test_validaciones_pre_h4.py` y pruebas frontend de errores, citas, factores, seguimiento, login y primer acceso. Los borrados no se restauran ni se borran físicamente; las restricciones existentes siguen reservando claves/órdenes históricos. La consulta de resultados históricos conserva su comportamiento.

El desempate se decide en dominio/aplicación usando carga y última asignación; quien nunca recibió una se ordena primero y correo/UUID estabilizan empates exactos. Se mantienen el bloqueo compartido y las restricciones existentes. Las páginas fuera del total devuelven una colección vacía sin enviar un OFFSET desbordado. El acceso administrativo sin perfil no habilita notas, resultados individuales ni alertas clínicas.

Pruebas negativas ejecutadas antes de corregir reprodujeron los fallos. La primera suite backend completa detectó una expectativa histórica 403 para cuentas borradas; se ajustó a 401 porque ahora JWT rechaza la cuenta antes de los permisos del recurso, manteniendo la denegación. La duplicidad de reglas de alerta ya era convertida a 400 por la transacción compartida y no se modificó.

## Decisiones no definidas

- La matriz permite ADMIN limitado a institución para usuarios/catálogos/instrumentos; las APIs existentes de esos módulos exigen SUPERADMIN. No hay alcance institucional delegado concretado en esos contratos: no se amplían privilegios automáticamente.
- No se inventan escalas clínicas para ánimo/intensidad/nivel ni estados cerrados para seguimiento. Permanecen los textos y límites actuales.
- Los rangos solapados se rechazan al clasificar, pero el catálogo permite configurarlos; falta concretar si deben prohibirse también al editar. La congelación completa del contenido de instrumentos ya utilizados tampoco está definida; PROTECT y respuestas inmutables no son una instantánea del texto del catálogo.

## Riesgos pendientes

- Esta revisión no sustituye T51–T55 tras T46/T48: faltan los escenarios de las funciones H4. T51 conserva En curso y ningún estado/fecha/criterio del Excel se modifica.
- Las pruebas frontend son de componentes/HTTP simulado. El E2E optativo de navegador requiere Angular/Playwright y habilitación explícita del entorno; una omisión no equivale a aprobación E2E.
- Se conserva la política actual de JWT sin blacklist/rotación: cerrar sesión en el navegador o cambiar contraseña no revoca todos los tokens ya emitidos. SQL directo y Django Admin no participan de todos los bloqueos de los casos de uso.
- No se añaden constraints redundantes ni migraciones. Las pruebas usan PostgreSQL temporal; SASPEL2 solo se consulta mediante `migrate --check`, sin cargar datos ni aplicar migraciones. No se lee/restaura el backup.
