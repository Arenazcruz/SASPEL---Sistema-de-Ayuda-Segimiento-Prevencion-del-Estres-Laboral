# SASPEL Hito 4

Para instalar las dependencias de Django, Angular y PostgreSQL, sigue el [README de la raíz](../../README.md). Configura la conexión y la clave JWT mediante el entorno local, ejecuta `python backend/manage.py migrate` y arranca Django y Angular. El frontend utiliza el origen de la API configurado en el proyecto.

El backend separa las decisiones de dominio, los casos de uso y los adaptadores Django/DRF. El JWT identifica al actor y la asignación profesional vigente limita los recursos visibles. Angular agrupa los casos por funcionalidad y delega el estado de cada vista a su ViewModel. PostgreSQL conserva la relación entre asignación, aplicación, respuestas y resultado. Consulta [relaciones y campos](DICCIONARIO.md) y [verificación física](INTEGRIDAD.md).

| Rol | Operación en la interfaz | Comprobación |
|---|---|---|
| Superadmin | Personas, roles, políticas y auditoría | Publicar una versión conserva las aceptaciones anteriores. Los filtros de auditoría trabajan sobre metadatos. |
| Administrador | Personal institucional, áreas, cargos, instrumentos, asignaciones y reportes | Puede gestionar trabajadores y psicólogos de la institución. El reporte de seguimiento institucional es agregado. |
| Nuevo trabajador | Cambiar contraseña, aceptar políticas, responder evaluación inicial | Tras finalizar se habilita Trabajador y se intenta la asignación profesional. |
| Trabajador | Mis instrumentos, resultados, evolución, citas, ánimo, factores, recomendaciones y notificaciones | Puede guardar avance y retomar. Las evaluaciones cerradas conservan su resultado. |
| Psicólogo | Mis trabajadores, agenda, resultados, alertas y seguimiento | Puede reprogramar conservando la cita anterior y registrar acciones con estado. Marcar **Compartir con el trabajador** publica solo el texto, estado y fecha de la recomendación. Las recomendaciones anteriores permanecen privadas. |

La evolución compara resultados registrados del mismo instrumento y versión. El historial de seguimiento y las notas de consulta quedan reservados a los profesionales autorizados.

**Comprobación técnica.** Desde la raíz, `python backend/tests/run_isolated.py tests` ejecuta la suite con un PostgreSQL temporal. En `frontend`, ejecuta `npm test -- --watch=false` y `npm run build`. Consulta [escenarios de navegador](E2E.md). La revisión final del esquema y la recuperación de la demo están en [el acta PostgreSQL](POSTGRES.md). La base oficial es SASPEL2. Para demostraciones, crea una base local vacía llamada `saspel_demo_h4`, apunta POSTGRES_DB a ella en la sesión de demostración, migra y ejecuta `python backend/manage.py seed_demo` con SASPEL_DEMO_PASSWORD definida. Repetir el seed conserva los avances y la contraseña que ya eligió cada persona.
