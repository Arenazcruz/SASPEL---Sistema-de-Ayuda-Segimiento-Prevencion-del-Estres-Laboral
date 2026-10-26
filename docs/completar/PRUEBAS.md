# Evidencia de pruebas y regresión

Ejecución local del 26/10/2026. Datos sintéticos. PostgreSQL 18 temporal con
autenticación SCRAM y `.env` deshabilitado. La base local solo recibió las tres
migraciones aditivas después de respaldo; no se usó para pruebas destructivas.

| Verificación | Resultado |
| --- | --- |
| Línea base backend | 428 descubiertas: 427 aprobadas, 1 navegador omitida por configuración; 0 fallos. |
| Línea base frontend | 209 aprobadas. |
| Suite backend final | 464 descubiertas: **462 aprobadas**, 2 navegador omitidas en esta ejecución; **0 fallos/errores**. |
| Suite exclusivamente versionada | **440 descubiertas: 438 aprobadas y 2 navegador omitidas**, ejecutada también sin incluir los tests locales ajenos. |
| Navegador separado | **2 aprobadas**, 0 omitidas/fallidas: Edge headless, Angular y API LiveServer real. |
| Suite frontend final | **222 aprobadas en 23 archivos**, 0 fallidas. |
| Verificación posterior de Admin/auditoría | 13 aprobadas después de ajustar ámbito de metadatos. Son repetición selectiva, no 13 casos nuevos. |
| Concurrencia nueva | 2 aprobadas, incluidas en suite: una sucesora por cita y una asignación pendiente por versión ante solicitudes simultáneas. |
| Angular producción | Compilación correcta; artefactos en `frontend/dist/frontend`. |
| Django | `check` sin incidencias; `makemigrations --check --dry-run` sin cambios pendientes. |
| Migración temporal | Instalación limpia, reversión 0015→0012 y reaplicación correctas. |
| Respaldo temporal | pg_dump/pg_restore a segunda BD; historial de migraciones y vínculo sintético recuperados. |
| Migración local | Respaldo previo verificado, 0013/0014/0015 aplicadas y conteos previos preservados. |

Los 464 casos backend incluyen **24 pruebas SQL locales preexistentes no
versionadas**, preservadas sin modificación ni incorporación a estos commits.
En un clon que no tenga ese archivo, la colección es de 440 casos (438 normales
y 2 de navegador). No se suman ejecuciones repetidas para inflar el total.

## Cobertura de escenarios

| Área | Evidencia y comprobaciones |
| --- | --- |
| Acceso y sesión | auth_api/auth_use_cases/login_attempts/primer_acceso/sesion_perfil; hash, rol vivo, cuenta inactiva, JWT malformado, revocación access y refresh, rotación al cambiar clave y no resurrección tras logout. |
| Admin institucional | institutional_admin: altas permitidas, rechazo de roles privilegiados, UUID directos protegidos, listado y resumen sin administradores, activar/desactivar sin borrar historial, catálogos/instrumentos y reasignación. |
| Área–cargo | Asociación activa, rechazo de UUID ajeno/inactivo y duplicados, rollback ante error, baja lógica y recuperación del mismo vínculo sin modificar perfiles. |
| Instrumentos/respuestas | responder_evaluacion/cierre_funcional: progreso persistido, reintento idempotente de finalización, respuestas posteriores rechazadas, dos aplicaciones independientes, sin repetir onboarding, versión usada inmutable. |
| Citas | citas_api/reprogramacion/cierre_concurrency: estados, razones, disponibilidad, cruces, origen conservado, carrera de dos reprogramaciones. |
| Resultados/evolución | resultados_historial/cierre_funcional: datos propios o de asignación vigente, exclusión de inválidos/borrados, orden temporal, dos versiones separadas, diferencia exacta, vacío y fechas inválidas. |
| Recomendaciones | Texto requerido, autor derivado de sesión, transición válida, estado terminal, privacidad frente a Admin/trabajador/profesional ajeno y reasignación. |
| Gobierno | gobierno: publicación por SA, versión previa conservada, nueva aceptación obligatoria, eventos actor/entidad sin texto/credenciales y consulta limitada. |
| Existentes preservados | Suites de asignaciones, notas, seguimiento, ánimo, factores, alertas, notificaciones, reportes, bootstrap, modelos, UUID y arquitectura. |
| Navegador | CRUD unificado y primer acceso; asignar instrumento, guardar/recargar/finalizar dos veces, gráfico y tabla, móvil sin desbordamiento, recomendación completada, perfil persistido, guard negativo y catálogos Admin con roles de alta limitados. |
| SQL y privacidad | Tests locales preexistentes, consultas parametrizadas, filtros/orden validado, GET sin escritura y CSV con neutralización de fórmulas. No equivale a prueba universal de penetración. |

## Fallos encontrados durante la iteración

Los primeros ensayos detectaron expectativas antiguas de cierre solo local,
tokens conservados tras cambiar contraseña y navegación Admin al panel genérico.
Se actualizaron para exigir los contratos nuevos, añadiendo comprobaciones de
revocación y cambio obligatorio de clave; no se eliminaron controles negativos.
Hubo errores de fixtures/selectores (código con guion bajo inválido, comparación
UUID/texto, nombre de test inexistente, selector que alcanzaba el filtro de roles
en vez del formulario y espera de polyline de altura cero). Se corrigieron las
fixtures y selectores manteniendo las reglas reales. Los ensayos finales arriba
no conservan fallos conocidos de esas iteraciones.

`test_uuid_audit` diferencia el modelo de evento append-only de las entidades
de negocio con baja lógica: verifica sus campos propios sin exigirle columnas
que permitirían editar o borrar el evento. El evento sigue validado por sus
pruebas específicas; no se excluyó para ocultar una falla.

## Evidencia y límites

En `evidencias/` se incluyen logs finales y capturas exclusivamente sintéticas:
evolución escritorio/móvil, recomendaciones y administración. El resumen JSON
registra hashes de los logs para detectar modificaciones. Los logs privados
intermedios permanecen en `.cache/completar/` y no se publican.

No se ejecutó SASPE-UF; no se midió carga institucional, latencia p95 objetivo,
compatibilidad en todos los motores ni accesibilidad con todas las ayudas
técnicas. No se obtuvo aceptación formal de usuarios, textos legales o entrega
académica. Estos límites explican el **94,59 % (70/74)** de requisitos verificados
de [MATRIZ.md](MATRIZ.md), sin declarar el proyecto completamente terminado.

Los comandos repetibles están en [GUIA.md](GUIA.md). Las capturas constituyen
evidencia de esos escenarios, no de todas las pantallas posibles.
