# Guion del Hito 4

Usa una base exclusiva y las cinco cuentas de `seed_demo`. El ensayo automático parte de una base nueva en cada ejecución. Para exposición manual usa la clave indicada al crear los datos. Las cuentas usan el dominio `@saspel.com`.

| Paso | Cuenta | Acciones | Evidencia observable |
|---|---|---|---|
| 1 | demo.sa | Entrar y abrir Políticas | Política de ensayo vigente, versión demo-1 |
| 2 | demo.admin | Abrir Personas | Buscar demo.trab y comprobar su alta institucional |
| 3 | demo.nuevo | Cambiar contraseña, aceptar política, comenzar evaluación, elegir la primera opción de las diez preguntas y finalizar | Resultado inicial y acceso al panel Trabajador |
| 4 | demo.trab | Abrir Mi evolución y Mis recomendaciones | Dos aplicaciones del instrumento H4-DEMO y una indicación compartida |
| 5 | demo.psi | Aceptar la cita solicitada, abrir Notificaciones y consultar el resultado que originó la alerta | Cita confirmada y detalle de evaluación autorizado |
| 6 | demo.trab | Consultar notificaciones | Aviso de cita confirmada |
| 7 | demo.admin, demo.sa | Consultar reporte de citas y exportar CSV. Como Superadmin, abrir Auditoría | Archivo descargado y eventos con fecha y actor |

**Ensayo reproducible.** Instala las dependencias y Edge antes de la exposición. Compila Angular en `frontend` con `npm run build`. Indica en `SASPEL_PLAYWRIGHT_MODULE` el módulo Playwright local y ejecuta desde la raíz `python backend/tests/run_isolated.py --browser tests.test_ensayo_browser`. La API y PostgreSQL usan datos efímeros. El guion cambia la contraseña y comprueba tres resultados al terminar.

**Plan B local.** La compilación, Edge, el servidor de archivos y PostgreSQL funcionan en el mismo equipo. Se puede repetir el ensayo sin conexión a GitHub. Si falla el proyector o el navegador, usa las capturas reales del paquete y el acta para explicar qué se ejecutó. Una exposición con capturas debe identificarse como tal.
