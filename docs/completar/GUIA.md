# Ejecución, demostración y recuperación

## Arranque local

Desde `C:\Users\jgabr\Documents\SASPEL`, conservar el `.env` privado existente.
El README describe Python, Node y PostgreSQL y las variables requeridas. No copiar
`.env.example` encima de una configuración existente. En esta máquina las
migraciones 0013–0015 ya se aplicaron con respaldo previo.

```powershell
.\.venv\Scripts\python.exe backend/manage.py check
.\.venv\Scripts\python.exe backend/manage.py migrate --plan
.\.venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000
```

En otra terminal:

```powershell
cd C:\Users\jgabr\Documents\SASPEL\frontend
npm.cmd start
```

Abrir `http://localhost:4200`. En otra instalación, preparar PostgreSQL y `.env`,
instalar dependencias fijadas, respaldar la base si ya contiene información y
ejecutar `backend/manage.py migrate` antes del servidor. La configuración Angular
de producción utiliza `/api`; el despliegue debe dirigirla a Django.

No se publicaron credenciales. Para una instalación nueva de desarrollo existe
`bootstrap_dev_superadmin`: usar las variables privadas
`SASPEL_DEV_SUPERADMIN_EMAIL` y `SASPEL_DEV_SUPERADMIN_PASSWORD`, con DEBUG local.
El comando no reemplaza arbitrariamente cuentas existentes. El catálogo
institucional y el instrumento inicial disponen de los comandos existentes
`seed_institution_catalogs` y `seed_initial_instrument`; revisar su configuración
aprobada antes de aplicarlos. Esta ejecución no sembró personas ni contenido de
demostración en la base habitual.

## Uso por rol y guion de demostración

Usar exclusivamente cuentas y datos sintéticos en una base de demostración.
Las fixtures de los tests crean escenarios repetibles; no importar datos de
SASPE-UF ni una base clínica real.

1. **Superadmin:** entrar a Personas, crear una cuenta Admin y un psicólogo
   habilitado. Configurar áreas, cargos y sus vínculos. Revisar el instrumento
   inicial y crear un instrumento de seguimiento con escala, opciones, preguntas
   y rangos configurados. No modificar una versión ya utilizada: crear otra.
2. **Admin:** entrar a Administración institucional. Registrar nuevo trabajador
   con código único; comprobar que no puede crear ADMIN/SUPERADMIN ni elegir
   TRABAJADOR directamente. Consultar lista y editar campos institucionales.
3. **Nuevo trabajador:** ingresar con la contraseña temporal, cambiarla, aceptar
   políticas pendientes, completar perfil inicial y resolver evaluación inicial.
   Guardar progreso, recargar y finalizar. Se obtiene rol TRABAJADOR y asignación
   por carga; si no hay psicólogos habilitados queda pendiente con aviso a Admin.
4. **Psicólogo:** en Mis trabajadores, asignar el instrumento de seguimiento.
   **Trabajador:** abrir Mis instrumentos, responder y finalizar. Repetir con
   otra asignación terminada para obtener dos puntos en Evolución.
5. **Evolución:** filtrar fechas y comprobar tabla/gráfico; versiones distintas
   permanecen separadas. La diferencia entre puntajes no es diagnóstico.
6. **Citas:** el psicólogo configura disponibilidad; el trabajador solicita cita;
   el psicólogo confirma o reprograma. La anterior queda REPROGRAMADA y la nueva
   conserva enlace al origen. Completar cita y registrar nota profesional.
7. **Seguimiento:** registrar motivo/categoría, observación, plan y revisión.
   Abrir Recomendaciones, escribir texto, iniciar y completar. Comprobar que
   trabajador/Admin no acceden al contenido privado.
8. **Ánimo, factores y alertas:** registrar datos sintéticos propios; revisar
   historial profesional. Configurar una regla explícita autorizada desde el
   panel habilitado y comprobar acciones de alerta, sin modelo predictivo.
9. **Administración:** consultar reportes operativos y CSV; no aparecen notas
   privadas. Superadmin consulta auditoría; Admin ve sus operaciones permitidas.
   Publicar únicamente texto de política aprobado, con nueva versión, y verificar
   que exige nueva aceptación cuando es obligatorio.
10. **Sesión y permisos:** cerrar sesión; access/refresh anteriores deben ser
    rechazados. Reasignar trabajador y comprobar que el profesional anterior
    pierde acceso. Desactivar una cuenta conserva su historial.

El ensayo automatizado ya ejecutado cubre los flujos descritos en PRUEBAS. Este
guion permite un ensayo institucional completo; su aprobación formal y la
presentación T67/T68 siguen pendientes.

## Pruebas reproducibles sin tocar la base habitual

El runner propio crea PostgreSQL temporal autenticado, verifica su directorio y
deshabilita `.env`. Se detiene y limpia solo ese directorio al terminar. Requiere
binarios PostgreSQL y las dependencias backend, no permisos sobre la base local.

```powershell
$env:SASPEL_TEST_PG_BIN='C:\Program Files\PostgreSQL\18\bin'
.\.venv\Scripts\python.exe backend/tests/run_isolated.py tests
.\.venv\Scripts\python.exe backend/tests/run_isolated.py --schema
cd frontend
npm.cmd test -- --watch=false
npm.cmd run build
```

Para navegador, dejar Angular en otra terminal:

```powershell
cd C:\Users\jgabr\Documents\SASPEL\frontend
npm.cmd start -- --host 127.0.0.1 --port 4300
```

Desde la raíz, ajustar `SASPEL_PLAYWRIGHT_MODULE` a un módulo Playwright disponible
y utilizar Edge instalado. No hace falta instalar librerías en el repositorio:

```powershell
$env:SASPEL_PLAYWRIGHT_MODULE='C:\Users\jgabr\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright'
$env:SASPEL_FRONTEND_URL='http://127.0.0.1:4300'
$env:SASPEL_SCREENSHOTS='C:\Users\jgabr\Documents\SASPEL\.cache\capturas-demo'
.\.venv\Scripts\python.exe backend/tests/run_isolated.py --browser tests.test_superadmin_browser tests.test_cierre_browser
```

El navegador redirige las peticiones a LiveServer de pruebas; nunca a la base
habitual. Las contraseñas se generan durante el test. Para el plan B local,
conservar las capturas sintéticas y los logs de evidencia, compilar Angular y
seguir este guion con una base exclusivamente de demostración. No se necesitan
servicios de correo, chat ni APIs externas.

## Respaldo y recuperación

El respaldo previo de esta máquina está en
`.cache/completar/respaldo-local/antes-0013-0015.dump`, con hash y verificación
en el JSON contiguo. Contiene información privada local: no adjuntarlo al repositorio.
La recuperación probada se hizo **en otra base temporal**, usando `pg_restore
--exit-on-error`, y comprobó tanto migraciones como un vínculo área–cargo sintético.

Para una recuperación real, crear una base de destino separada, restaurar allí,
validar esquema y conteos y solo después decidir el cambio de conexión. No usar
`--clean`, DROP DATABASE ni reversión de tablas con datos sobre la base actual.
Las migraciones son reversibles técnicamente, pero quitar recomendaciones o
auditoría eliminaría registros incorporados después del respaldo.

## Pendientes de aceptación

RNF-18: validación integral de usabilidad con usuarios. RNF-19: matriz de tablets
y navegadores adicionales a Edge. RNF-20: volumen y tiempos objetivo acordados,
prueba de carga y medición. RNF-24: comprobar una extensión futura real sin
alterar el núcleo; la arquitectura ya la facilita. Revisar institucionalmente
textos legales e instrumentos antes de uso real. No se afirma aprobación jurídica,
despliegue público, migración de datos de Laravel ni cierre académico T68.
