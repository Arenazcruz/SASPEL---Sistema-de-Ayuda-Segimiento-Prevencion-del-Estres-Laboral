# Completar SASPEL desde la referencia SASPE-UF

Fecha: 26/10/2026. Rama: `codex/completar-saspel-referencia`, creada desde
`feature/auditoria-validaciones-pre-h4`. Se conserva la base integrada y los
archivos locales de auditoría SQL y gestión, que no forman parte de estos commits.

## Alcance y fuentes

Se comprobaron ambas rutas, el cronograma y la URL de origin. Las 12 hojas del
cronograma se leen sin modificar el archivo. RF/RN/Roles prevalecen sobre Laravel;
los estados de hojas auxiliares no se toman como evidencia de implementación.
SASPE-UF se consulta estáticamente, sin ejecutar Artisan ni acceder a sus datos.

## Orden de implementación

1. Auditoría e inventario de rutas, modelos, servicios, vistas y pruebas de ambos
   proyectos. Establecer línea base backend/frontend sobre datos sintéticos.
2. T46 / RF-27–29: reprogramación atómica con vínculo al horario original,
   permisos, disponibilidad, solapamientos y regresión de concurrencia.
3. T47 / RF-19–23: asignación profesional, listado propio y resolución posterior
   al onboarding; reutilizar el motor probado sin repetir transición de rol.
4. T48 / RF-36: recomendaciones manuales vinculadas al seguimiento y estado.
5. T49 / RF-47–48: evolución por instrumento/version, periodo y resultados
   válidos; tendencia descriptiva sin comparar escalas incompatibles.
6. T44/T45 / RF-45–46,49: trazabilidad consultable sin contenido clínico y
   publicación de versiones de políticas con aceptación renovada.
7. T50/T51: eventos de los nuevos flujos, navegación, carga, vacío y errores.
8. T52–66: pruebas de permisos, límites, integración, migraciones, compilación,
   documentación, matriz RF→código→evidencia y guía reproducible de demostración.

## Límites

No se cambian el Excel ni el informe académico. No se publica ni integra a
main/develop. No se inventan parámetros clínicos ni textos legales aprobados.
El usuario confirmó el 26/10/2026 que SASPEL representa una sola institución.
ADMIN gestiona sus trabajadores, psicólogos, catálogos, instrumentos y
reasignaciones mediante una superficie acotada; los roles y cuentas
administrativas globales permanecen reservados a SUPERADMIN. No se añade una
entidad multiinstitución. También se completa la vinculación área–cargo.
Chat, diario, IA y recomendaciones automáticas no se incorporan.
Cada resultado de pruebas se registra con sus omisiones. Los cambios de esquema
se verifican en PostgreSQL aislado antes de considerar su aplicación real.
