# Matriz de escenarios en navegador

| Rol | Acción y comprobación observable | Prueba reproducible |
|---|---|---|
| Superadmin y nuevo trabajador | Crear cuenta, consultarla, cambiar contraseña temporal e ingresar | `tests.test_superadmin_browser` |
| Psicólogo y trabajador | Asignar y resolver dos aplicaciones, guardar y recargar respuestas, consultar historial y evolución, ver la gráfica y la tabla en móvil | `tests.test_cierre_browser` |
| Trabajador y psicólogo | Registrar ánimo, solicitar/confirmar cita, marcar aviso leído, atender alerta y consultar seguimiento | Mismo recorrido, datos y API reales |
| Psicólogo | Crear una recomendación, iniciarla y completarla | Mismo recorrido |
| Admin | Crear y asociar cargo y área, verificar los roles habilitados para alta, consultar reportes y auditoría | Mismo recorrido |

Ejecución con PostgreSQL efímero y Edge en modo headless. Ambos escenarios finalizaron correctamente. Las capturas de `evidencias/` corresponden a los usuarios ficticios de esa ejecución. Los guiones de navegador están en `frontend/e2e/`.
