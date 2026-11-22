# Trazabilidad funcional H4

Las rutas son relativas a `/api/`. Cada fila HU/CU enlaza al requisito que materializa la acción. Las RN conservan las relaciones originales del cronograma. RF-50, lógica difusa, IA, ML y Markov predictivo pertenecen al aporte futuro.

| RF | Función | Módulo y pantalla | Ruta de entrada | Prueba |
|---|---|---|---|---|
| RF-01 | El sistema debe permitir iniciar sesión mediante credenciales institucionales. | Acceso y seguridad · Ingreso | `auth/login/` | [test_auth_api](../../backend/tests/test_auth_api.py), [test_auth_use_cases](../../backend/tests/test_auth_use_cases.py) |
| RF-02 | El sistema debe permitir cerrar la sesión de forma segura. | Acceso y seguridad · Cerrar sesión | `auth/logout/` | [test_auth_api](../../backend/tests/test_auth_api.py), [test_auth_use_cases](../../backend/tests/test_auth_use_cases.py) |
| RF-03 | El sistema debe permitir cambiar una contraseña temporal en el primer acceso. | Acceso y seguridad · Cambiar contraseña | `auth/primer-acceso/password/` | [test_auth_api](../../backend/tests/test_auth_api.py), [test_auth_use_cases](../../backend/tests/test_auth_use_cases.py) |
| RF-04 | El sistema debe registrar la aceptación de las políticas de uso, privacidad y tratamiento de información vigentes. | Acceso y seguridad · Políticas de primer acceso | `auth/primer-acceso/aceptar/` | [test_auth_api](../../backend/tests/test_auth_api.py), [test_auth_use_cases](../../backend/tests/test_auth_use_cases.py) |
| RF-05 | El sistema debe redirigir al usuario al dashboard correspondiente según su rol. | Acceso y seguridad · Panel por rol | `dashboard/` | [test_auth_api](../../backend/tests/test_auth_api.py), [test_auth_use_cases](../../backend/tests/test_auth_use_cases.py) |
| RF-06 | El sistema debe permitir completar y consultar el perfil institucional del usuario. | Usuarios y perfiles · Mi perfil | `perfil/` | [test_sesion_perfil](../../backend/tests/test_sesion_perfil.py) |
| RF-07 | El sistema debe permitir al Administrador registrar trabajadores y psicólogos de la institución. | Usuarios y perfiles · Personas | `institucional/users/` | [test_institutional_admin](../../backend/tests/test_institutional_admin.py), [test_superadmin_api](../../backend/tests/test_superadmin_api.py) |
| RF-08 | El sistema debe permitir activar o desactivar cuentas institucionales sin eliminar su historial. | Usuarios y perfiles · Personas | `institucional/users/{id}/deactivate/` | [test_institutional_admin](../../backend/tests/test_institutional_admin.py), [test_superadmin_api](../../backend/tests/test_superadmin_api.py) |
| RF-09 | El sistema debe permitir al Superadministrador gestionar usuarios y roles de forma global. | Usuarios y perfiles · Gestión global de usuarios | `superadmin/users/{id}/role/` | [test_superadmin_api](../../backend/tests/test_superadmin_api.py), [test_institutional_admin](../../backend/tests/test_institutional_admin.py) |
| RF-10 | Todo trabajador recién registrado debe iniciar como Nuevo Trabajador y acceder a un dashboard de bienvenida y orientación. | Onboarding · Bienvenida | `nuevo-trabajador/dashboard/` | [test_nuevo_trabajador_dashboard](../../backend/tests/test_nuevo_trabajador_dashboard.py), [test_responder_evaluacion](../../backend/tests/test_responder_evaluacion.py) |
| RF-11 | El sistema debe permitir al Nuevo Trabajador realizar la evaluación inicial obligatoria. | Onboarding · Mi evaluación inicial | `nuevo-trabajador/evaluaciones/{id}/` | [test_nuevo_trabajador_dashboard](../../backend/tests/test_nuevo_trabajador_dashboard.py), [test_responder_evaluacion](../../backend/tests/test_responder_evaluacion.py) |
| RF-12 | Al completar correctamente la evaluación inicial, el sistema debe cambiar el rol de Nuevo Trabajador a Trabajador. | Onboarding · Finalización inicial | `nuevo-trabajador/evaluaciones/{id}/finalizar/` | [test_nuevo_trabajador_dashboard](../../backend/tests/test_nuevo_trabajador_dashboard.py), [test_responder_evaluacion](../../backend/tests/test_responder_evaluacion.py) |
| RF-13 | El sistema debe asignar automáticamente al nuevo Trabajador a un Psicólogo habilitado con la menor carga activa. | Asignación profesional · Resultado inicial y asignaciones | `nuevo-trabajador/evaluaciones/{id}/finalizar/` | [test_assignments_api](../../backend/tests/test_assignments_api.py), [test_assignments_concurrency](../../backend/tests/test_assignments_concurrency.py) |
| RF-14 | Cuando exista empate de carga, el sistema debe priorizar al Psicólogo que lleve más tiempo sin recibir una nueva asignación. | Asignación profesional · Distribución profesional y asignación en finalización inicial | `institucional/assignments/psychologists/` | [test_assignments_api](../../backend/tests/test_assignments_api.py), [test_assignments_concurrency](../../backend/tests/test_assignments_concurrency.py) |
| RF-15 | Si no existen Psicólogos disponibles, el sistema debe dejar la asignación pendiente y notificar al área administrativa. | Asignación profesional · Avisos administrativos después de finalizar | `notificaciones/` | [test_assignments_api](../../backend/tests/test_assignments_api.py), [test_assignments_concurrency](../../backend/tests/test_assignments_concurrency.py) |
| RF-16 | El sistema debe permitir reasignar un Trabajador conservando el historial de asignaciones anteriores. | Asignación profesional · Asignaciones profesionales | `institucional/assignments/{id}/reassign/` | [test_assignments_api](../../backend/tests/test_assignments_api.py), [test_assignments_concurrency](../../backend/tests/test_assignments_concurrency.py) |
| RF-17 | El sistema debe permitir administrar instrumentos psicológicos y su estado activo/inactivo. | Instrumentos psicológicos · Instrumentos | `institucional/instruments/` | [test_instruments_api](../../backend/tests/test_instruments_api.py), [test_instrument_content_api](../../backend/tests/test_instrument_content_api.py) |
| RF-18 | El sistema debe permitir administrar preguntas, opciones de respuesta, orden y rangos de interpretación por instrumento. | Instrumentos psicológicos · Preguntas, escalas y rangos | `institucional/instruments/{id}/questions/` | [test_instruments_api](../../backend/tests/test_instruments_api.py), [test_instrument_content_api](../../backend/tests/test_instrument_content_api.py) |
| RF-19 | El sistema debe permitir asignar instrumentos a Trabajadores para su resolución. | Instrumentos psicológicos · Mis trabajadores, asignar instrumento | `psicologo/trabajadores/{id}/instrumentos/` | [test_cierre_funcional](../../backend/tests/test_cierre_funcional.py) |
| RF-20 | El Trabajador debe poder consultar los instrumentos que tiene asignados y su estado. | Instrumentos psicológicos · Mis instrumentos | `trabajador/instrumentos/` | [test_cierre_funcional](../../backend/tests/test_cierre_funcional.py) |
| RF-21 | El Trabajador debe poder responder y finalizar un instrumento asignado. | Instrumentos psicológicos · Responder evaluación | `trabajador/evaluaciones/{id}/finalizar/` | [test_cierre_funcional](../../backend/tests/test_cierre_funcional.py) |
| RF-22 | Una aplicación finalizada no debe permitir modificar sus respuestas. | Instrumentos psicológicos · Evaluación finalizada | `trabajador/evaluaciones/{id}/respuestas/` | [test_cierre_funcional](../../backend/tests/test_cierre_funcional.py), [test_cierre_concurrency](../../backend/tests/test_cierre_concurrency.py) |
| RF-23 | El sistema debe calcular el puntaje y determinar el rango de interpretación configurado para el instrumento. | Instrumentos psicológicos · Resultado al finalizar | `trabajador/evaluaciones/{id}/finalizar/` | [test_cierre_funcional](../../backend/tests/test_cierre_funcional.py), [test_cierre_concurrency](../../backend/tests/test_cierre_concurrency.py) |
| RF-24 | El Trabajador debe poder consultar sus resultados e historial de instrumentos resueltos. | Resultados · Mis resultados | `trabajador/resultados/` | [test_resultados_historial](../../backend/tests/test_resultados_historial.py) |
| RF-25 | El Psicólogo debe poder consultar los resultados e historial de los Trabajadores que tenga asignados. | Resultados · Resultados del trabajador | `psicologo/trabajadores/{id}/resultados/` | [test_resultados_historial](../../backend/tests/test_resultados_historial.py) |
| RF-26 | El Trabajador debe poder solicitar una cita con el Psicólogo que tenga asignado. | Citas · Solicitar cita | `citas/` | [test_citas_api](../../backend/tests/test_citas_api.py), [test_reprogramacion](../../backend/tests/test_reprogramacion.py) |
| RF-27 | El Psicólogo debe poder aprobar, rechazar, reprogramar o cancelar solicitudes de cita de sus Trabajadores asignados. | Citas · Agenda y citas | `citas/{id}/reprogramar/` | [test_citas_api](../../backend/tests/test_citas_api.py), [test_reprogramacion](../../backend/tests/test_reprogramacion.py) |
| RF-28 | El sistema debe impedir solapamientos de horarios para un mismo Psicólogo. | Citas · Solicitar cita | `citas/` | [test_citas_api](../../backend/tests/test_citas_api.py), [test_reprogramacion](../../backend/tests/test_reprogramacion.py) |
| RF-29 | Trabajador y Psicólogo deben poder consultar sus citas y el estado de cada una. | Citas · Historial de citas | `citas/` | [test_citas_api](../../backend/tests/test_citas_api.py), [test_reprogramacion](../../backend/tests/test_reprogramacion.py) |
| RF-30 | El Psicólogo debe poder registrar una nota asociada a una cita realizada. | Citas · Notas profesionales | `citas/{id}/notas/` | [test_notas_cita](../../backend/tests/test_notas_cita.py) |
| RF-31 | El Trabajador debe poder registrar su estado de ánimo para construir un historial temporal. | Monitoreo emocional · Mi estado de ánimo | `trabajador/animo/` | [test_estado_animo](../../backend/tests/test_estado_animo.py) |
| RF-32 | El Trabajador debe poder registrar factores psicosociales relevantes de su entorno laboral. | Factores psicosociales · Mis factores psicosociales | `trabajador/factores/` | [test_factores](../../backend/tests/test_factores.py) |
| RF-33 | El Psicólogo debe poder consultar el historial de factores psicosociales de sus Trabajadores asignados. | Factores psicosociales · Factores del trabajador | `psicologo/trabajadores/{id}/factores/` | [test_factores](../../backend/tests/test_factores.py) |
| RF-34 | El Psicólogo debe poder registrar observaciones, motivo, categoría, plan de acción y próxima revisión de un seguimiento. | Seguimiento profesional · Seguimiento profesional | `psicologo/trabajadores/{id}/seguimiento/` | [test_seguimiento](../../backend/tests/test_seguimiento.py), [test_cierre_funcional](../../backend/tests/test_cierre_funcional.py) |
| RF-35 | El sistema debe mantener el historial cronológico de seguimientos de cada Trabajador. | Seguimiento profesional · Historial de seguimiento | `psicologo/trabajadores/{id}/seguimiento/` | [test_seguimiento](../../backend/tests/test_seguimiento.py), [test_cierre_funcional](../../backend/tests/test_cierre_funcional.py) |
| RF-36 | El Psicólogo debe poder registrar recomendaciones profesionales asociadas a un seguimiento. | Recomendaciones · Recomendaciones del seguimiento | `seguimientos/{id}/recomendaciones/` | [test_recomendacion_compartida](../../backend/tests/test_recomendacion_compartida.py), [test_seguimiento](../../backend/tests/test_seguimiento.py) |
| RF-37 | El sistema debe poder generar alertas de riesgo mediante reglas explícitas de negocio configuradas para el alcance actual. | Alertas · Reglas de alerta y resultados finalizados | `alertas/reglas/` | [test_alertas](../../backend/tests/test_alertas.py) |
| RF-38 | El Psicólogo debe poder revisar, atender y cerrar alertas de sus Trabajadores asignados. | Alertas · Alertas de trabajadores asignados | `alertas/{id}/acciones/` | [test_alertas](../../backend/tests/test_alertas.py) |
| RF-39 | Cada acción realizada sobre una alerta debe quedar registrada como seguimiento de la alerta. | Alertas · Historial de acciones de alerta | `alertas/` | [test_alertas](../../backend/tests/test_alertas.py) |
| RF-40 | El sistema debe generar notificaciones relacionadas con asignaciones, instrumentos, citas, alertas y otros eventos funcionales. | Notificaciones · Centro de notificaciones | `notificaciones/` | [test_notificaciones](../../backend/tests/test_notificaciones.py) |
| RF-41 | Los usuarios deben poder consultar y marcar sus notificaciones como leídas. | Notificaciones · Marcar como leída | `notificaciones/{id}/leer/` | [test_notificaciones](../../backend/tests/test_notificaciones.py), [test_cierre_funcional](../../backend/tests/test_cierre_funcional.py) |
| RF-42 | El Administrador debe poder gestionar áreas y cargos institucionales utilizados por los perfiles. | Administración · Configurar cargos por área | `institucional/areas/{id}/cargos/` | [test_superadmin_api](../../backend/tests/test_superadmin_api.py), [test_institutional_admin](../../backend/tests/test_institutional_admin.py) |
| RF-43 | El Administrador debe poder consultar información operativa y estadísticas institucionales sin acceder por defecto a notas psicológicas privadas. | Administración · Panel administrativo | `dashboard/` | [test_dashboard](../../backend/tests/test_dashboard.py), [test_reportes](../../backend/tests/test_reportes.py) |
| RF-44 | El sistema debe permitir generar reportes operativos de usuarios, instrumentos, citas y seguimiento según permisos. | Reportes · Reportes operativos | `reportes/citas/` | [test_dashboard](../../backend/tests/test_dashboard.py), [test_reportes](../../backend/tests/test_reportes.py) |
| RF-45 | El sistema debe registrar acciones administrativas y sensibles para permitir trazabilidad. | Auditoría · Auditoría funcional | `administracion/auditoria/` | [test_gobierno](../../backend/tests/test_gobierno.py) |
| RF-46 | El sistema debe conservar las versiones de políticas y el registro de aceptación de cada usuario. | Políticas y privacidad · Políticas institucionales | `administracion/politicas/` | [test_gobierno](../../backend/tests/test_gobierno.py), [test_superadmin_api](../../backend/tests/test_superadmin_api.py) |
| RF-47 | El sistema debe permitir al Trabajador consultar la evolución histórica de sus niveles de estrés a partir de evaluaciones registradas. | Evolución · Mi evolución del estrés | `trabajador/evolucion/` | [test_cierre_funcional](../../backend/tests/test_cierre_funcional.py) |
| RF-48 | El sistema debe permitir al Psicólogo consultar la evolución histórica y tendencia de los trabajadores que tenga asignados, respetando los permisos de acceso. | Evolución · Evolución del trabajador | `psicologo/trabajadores/{id}/evolucion/` | [test_cierre_funcional](../../backend/tests/test_cierre_funcional.py) |
| RF-49 | El Superadministrador debe poder gestionar configuración global, usuarios, instrumentos y auditoría del sistema. | Superadministración · Gestión global y configuración | `superadmin/users/` | [test_gobierno](../../backend/tests/test_gobierno.py), [test_superadmin_api](../../backend/tests/test_superadmin_api.py) |

## HistoriasUsuario

| ID | Escenario | Fila funcional |
|---|---|---|
| HU-01 | Cambiar contraseña temporal | RF-03 |
| HU-02 | Aceptar políticas de privacidad | RF-04 |
| HU-03 | Completar perfil inicial | RF-06 |
| HU-04 | Ver dashboard de bienvenida | RF-10 |
| HU-05 | Resolver evaluación inicial | RF-11 |
| HU-06 | Ser habilitado como Trabajador | RF-12 |
| HU-07 | Recibir asignación automática de Psicólogo | RF-13 |
| HU-08 | Iniciar sesión | RF-01 |
| HU-09 | Cerrar sesión | RF-02 |
| HU-10 | Visualizar dashboard principal | RF-05 |
| HU-11 | Consultar perfil | RF-06 |
| HU-12 | Consultar instrumentos asignados | RF-20 |
| HU-13 | Resolver instrumento asignado | RF-21 |
| HU-14 | Consultar historial de resultados | RF-24 |
| HU-15 | Registrar estado de ánimo | RF-31 |
| HU-16 | Registrar factor psicosocial | RF-32 |
| HU-17 | Solicitar cita | RF-26 |
| HU-18 | Consultar mis citas | RF-29 |
| HU-19 | Consultar notificaciones | RF-40 |
| HU-20 | Marcar notificación como leída | RF-41 |
| HU-21 | Consultar mi evolución del estrés | RF-47 |
| HU-22 | Visualizar dashboard de Psicólogo | RF-05 |
| HU-23 | Consultar trabajadores asignados | RF-13 / RF-25 · `psicologo/trabajadores/` · Mis trabajadores · test_resultados_historial |
| HU-24 | Revisar resultados de un trabajador | RF-25 |
| HU-25 | Asignar instrumento | RF-19 |
| HU-26 | Resolver solicitud de cita | RF-27 |
| HU-27 | Consultar agenda | RF-29 |
| HU-28 | Registrar nota de cita | RF-30 |
| HU-29 | Registrar seguimiento profesional | RF-34 |
| HU-30 | Consultar estado de ánimo y factores | RF-31 / RF-33 · `psicologo/trabajadores/{id}/animo/` y `factores/` · test_estado_animo / test_factores |
| HU-31 | Atender alerta de riesgo | RF-38 |
| HU-32 | Registrar recomendación profesional | RF-36 |
| HU-33 | Consultar evolución de un trabajador | RF-48 |
| HU-34 | Visualizar dashboard administrativo | RF-43 |
| HU-35 | Registrar trabajador | RF-07 |
| HU-36 | Registrar Psicólogo | RF-07 |
| HU-37 | Activar o desactivar usuario | RF-08 |
| HU-38 | Revisar asignaciones profesionales | RF-16 |
| HU-39 | Gestionar áreas y cargos | RF-42 |
| HU-40 | Gestionar instrumentos | RF-17 |
| HU-41 | Consultar reportes institucionales | RF-44 |
| HU-42 | Visualizar dashboard global | RF-05 |
| HU-43 | Gestionar usuarios y roles globales | RF-09 |
| HU-44 | Gestionar versiones de políticas | RF-46 |
| HU-45 | Consultar auditoría | RF-45 |
| HU-46 | Gestionar configuración global | RF-49 |
| HU-47 | Recibir aviso cuando no exista Psicólogo disponible | RF-15 |
| HU-48 | Reasignar trabajador conservando historial | RF-16 |
| HU-49 | Consultar notificaciones profesionales | RF-40 |
| HU-50 | Consultar auditoría institucional permitida | RF-45 |

## CasosUso

| ID | Escenario | Fila funcional |
|---|---|---|
| CU-01 | Iniciar sesión | RF-01 |
| CU-02 | Cerrar sesión | RF-02 |
| CU-03 | Aceptar políticas | RF-04 |
| CU-04 | Completar perfil inicial | RF-06 |
| CU-05 | Realizar evaluación inicial | RF-11 |
| CU-06 | Asignar Psicólogo automáticamente | RF-13 |
| CU-07 | Registrar usuario institucional | RF-07 |
| CU-08 | Activar o desactivar usuario | RF-08 |
| CU-09 | Gestionar instrumento | RF-17 |
| CU-10 | Gestionar preguntas y opciones | RF-18 |
| CU-11 | Asignar instrumento | RF-19 |
| CU-12 | Resolver instrumento | RF-21 |
| CU-13 | Calcular resultado | RF-23 |
| CU-14 | Consultar resultados | RF-24 / RF-25 |
| CU-15 | Solicitar cita | RF-26 |
| CU-16 | Resolver solicitud de cita | RF-27 |
| CU-17 | Registrar nota de cita | RF-30 |
| CU-18 | Registrar estado de ánimo | RF-31 |
| CU-19 | Registrar factor psicosocial | RF-32 |
| CU-20 | Registrar seguimiento profesional | RF-34 |
| CU-21 | Generar alerta por regla | RF-37 |
| CU-22 | Atender alerta | RF-38 |
| CU-23 | Generar notificación | RF-40 |
| CU-24 | Consultar notificaciones | RF-41 |
| CU-25 | Consultar distribución de Psicólogos | RF-14 |
| CU-26 | Reasignar Trabajador | RF-16 |
| CU-27 | Registrar recomendación | RF-36 |
| CU-28 | Gestionar políticas | RF-46 |
| CU-29 | Consultar auditoría | RF-45 |
| CU-30 | Consultar evolución del estrés | RF-47 |

## Reglas de negocio

| Regla | Condición | Requisito y evidencia |
|---|---|---|
| RN-USR-01 | Todo trabajador recién registrado inicia con el rol NUEVO_TRABAJADOR. | RF-10 |
| RN-USR-02 | NUEVO_TRABAJADOR solo accede al flujo de onboarding, perfil inicial, políticas y evaluación inicial. | RF-10, RF-11 |
| RN-USR-03 | Al finalizar correctamente la evaluación inicial, el rol cambia automáticamente a TRABAJADOR. | RF-12 |
| RN-USR-04 | La desactivación de una cuenta no elimina su información histórica. | RF-08 |
| RN-USR-05 | SUPERADMIN utiliza los privilegios globales de administración, pero no obtiene por defecto acceso funcional a notas psicológicas privadas. | RF-09, RF-49 |
| RN-USR-06 | ADMIN gestiona usuarios y datos institucionales, pero no debe acceder por defecto al contenido sensible de seguimiento profesional. | RF-43 |
| RN-ASG-01 | Todo TRABAJADOR debe tener como máximo una asignación profesional activa. | RF-13 |
| RN-ASG-02 | Al completar el onboarding, el sistema asigna al Trabajador a un Psicólogo activo y habilitado para recibir asignaciones. | RF-13 |
| RN-ASG-03 | Se selecciona al Psicólogo con menor cantidad de Trabajadores con asignación activa. | RF-13 |
| RN-ASG-04 | Si existe empate de carga, se prioriza al Psicólogo que lleve más tiempo sin recibir una nueva asignación. | RF-14 |
| RN-ASG-05 | Un Psicólogo inactivo o no habilitado no puede recibir nuevas asignaciones. | RF-13 |
| RN-ASG-06 | Si no existe Psicólogo disponible, la asignación queda pendiente y Administración debe ser notificada. | RF-15 |
| RN-ASG-07 | Una reasignación finaliza la asignación activa anterior y crea una nueva, preservando el historial. | RF-16 |
| RN-INS-01 | Solo instrumentos activos pueden ser asignados o utilizados en nuevas aplicaciones. | RF-17 |
| RN-INS-02 | Las preguntas pertenecen a un único instrumento y mantienen un orden definido. | RF-18 |
| RN-INS-03 | Las opciones de respuesta y sus valores pertenecen a una escala de respuesta; las preguntas de tipo escala utilizan la escala correspondiente y pueden compartir sus opciones. | RF-18 |
| RN-INS-04 | La evaluación inicial debe estar identificada como instrumento de onboarding y estar disponible para NUEVO_TRABAJADOR. | RF-11 |
| RN-INS-05 | Una asignación de instrumento identifica al Trabajador, instrumento y responsable que realizó la asignación. | RF-19 |
| RN-INS-06 | Una aplicación finalizada no puede modificar sus respuestas. | RF-22 |
| RN-INS-07 | El resultado se calcula usando las respuestas y reglas/rangos configurados para el instrumento correspondiente. | RF-23 |
| RN-INS-08 | Los niveles o rangos de interpretación no constituyen por sí solos un diagnóstico clínico. | RF-23, RNF-07 |
| RN-CIT-01 | Un Trabajador solo puede solicitar cita con el Psicólogo de su asignación profesional activa. | RF-26 |
| RN-CIT-02 | Una cita puede transitar entre SOLICITADA, CONFIRMADA, REPROGRAMADA, COMPLETADA, CANCELADA o RECHAZADA. | RF-27 |
| RN-CIT-03 | No se pueden confirmar dos citas solapadas para el mismo Psicólogo. | RF-28 |
| RN-CIT-04 | Una nota de cita solo puede ser registrada por el Psicólogo asociado a la asignación correspondiente. | RF-30 |
| RN-CIT-05 | El historial de citas debe conservarse aun cuando una cita sea cancelada o rechazada. | RF-29 |
| RN-SEG-01 | El Psicólogo solo puede registrar seguimiento sobre Trabajadores que tenga asignados activamente. | RF-34 |
| RN-SEG-02 | Cada seguimiento debe registrar fecha, motivo/categoría, observación y responsable. | RF-34 |
| RN-SEG-03 | Las recomendaciones profesionales se asocian a un seguimiento y no se presentan como diagnóstico automático. | RF-36 |
| RN-SEG-04 | Los registros de estado de ánimo y factores psicosociales pertenecen al Trabajador que los registró y forman parte de su historial. | RF-31, RF-32 |
| RN-ALT-01 | Las alertas del alcance H2-H4 se generan únicamente mediante reglas explícitas de negocio, no mediante IA o modelos predictivos. | RF-37 |
| RN-ALT-02 | Cada alerta tiene estado y nivel de atención, y sus acciones de seguimiento deben quedar trazadas. | RF-38, RF-39 |
| RN-ALT-03 | El Psicólogo solo puede gestionar alertas de Trabajadores dentro de su asignación autorizada. | RF-38 |
| RN-NOT-01 | Las notificaciones se dirigen a usuarios específicos y deben conservar estado de lectura. | RF-40, RF-41 |
| RN-PRI-01 | La información personal y emocional se consulta bajo el principio de mínimo acceso necesario. | RNF-03, RNF-04 · test_cierre_funcional / test_gobierno |
| RN-PRI-02 | Las políticas deben versionarse y cada aceptación debe identificar usuario, versión y fecha. | RF-46 |
| RN-PRI-03 | Una nueva versión obligatoria de política requiere nueva aceptación del usuario. | RF-46 |
| RN-AUD-01 | Las acciones administrativas y sensibles definidas por el sistema deben registrar actor, acción, entidad afectada y fecha. | RF-45 |
| RN-EVO-01 | La evolución del estrés debe construirse a partir de resultados históricos válidos y no debe modificar evaluaciones anteriores. | RF-47, RF-48 |
| RN-DB-01 | El modelo físico propio de SASPEL debe mantenerse en Tercera Forma Normal salvo excepción técnica documentada. | RNF-11 · test_uuid_audit / test_esquema_h4 |
