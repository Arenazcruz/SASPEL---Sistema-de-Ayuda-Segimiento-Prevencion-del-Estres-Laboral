# SASPEL

Sistema de Ayuda, Seguimiento y Prevención del Estrés Laboral.

Tecnologías principales: Python, Django, Django REST Framework y PostgreSQL
en un backend de Arquitectura Hexagonal; Angular y TypeScript en un frontend
organizado con MVVM + Features.

```text
backend/   API, dominio, casos de uso, persistencia, migraciones y pruebas
frontend/  Aplicación Angular, vistas, ViewModels y pruebas
docs/      Guías de uso, informes de implementación y estrategia Git
```

Consulta la [estrategia de ramas](docs/ESTRATEGIA_GIT.md): `main` contiene
versiones estables, `develop` integra funcionalidades terminadas y `feature/*`
aloja el desarrollo. `feature/asignacion-profesional` está reservada para T23.

## Instalación básica

Requisitos: Git, Python compatible con `backend/requirements.txt`, PostgreSQL
en ejecución y Node.js/npm compatibles con Angular 21. Las dependencias del
backend están fijadas en requirements y las del frontend en package-lock.

```powershell
git clone https://github.com/Arenazcruz/SASPEL---Sistema-de-Ayuda-Segimiento-Prevencion-del-Estres-Laboral.git SASPEL
cd SASPEL
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Crea una base PostgreSQL vacía y configura en `.env` las variables descritas
abajo, con valores privados propios. El repositorio no incluye la base real.
Después aplica el esquema versionado e inicia el backend:

```powershell
.\.venv\Scripts\python.exe backend/manage.py migrate
.\.venv\Scripts\python.exe backend/manage.py runserver
```

En otra terminal, desde `frontend`, ejecuta `npm.cmd ci` y `npm.cmd start`.
Abre `http://localhost:4200`; la API local está en `http://127.0.0.1:8000/api/`.
Para el primer acceso administrativo en desarrollo, configura las variables
`SASPEL_DEV_SUPERADMIN_EMAIL` y `SASPEL_DEV_SUPERADMIN_PASSWORD` de tu `.env`
y ejecuta `.\.venv\Scripts\python.exe backend/manage.py bootstrap_dev_superadmin`
desde la raíz con `DJANGO_DEBUG=True`.

La compilación de producción usa `/api`: el servidor de despliegue debe dirigir
esa ruta al backend. La configuración de desarrollo usa el backend local.

## Verificaciones antes de integrar

Desde `backend`, con PostgreSQL disponible y un usuario con permiso `CREATEDB`
para que Django cree y elimine su base de pruebas separada:

```powershell
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py test --noinput --verbosity 1
..\.venv\Scripts\python.exe -m pip check
..\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

El proyecto utiliza el runner de Django; pytest no forma parte de sus
dependencias ni tiene configuración en esta versión.

Desde `frontend`:

```powershell
npm.cmd test -- --watch=false
npm.cmd run build
```

Si una comprobación falla, no integrar ni publicar el cambio como estable.

## Estado e historial de implementación

**Estado actual de esta rama:** T23 incorpora asignaciones profesionales manuales
en Superadmin, con carga de psicólogos, trabajadores sin asignación, finalización,
reasignación e historial. Consulta [implementación y pruebas de T23](docs/T23_IMPLEMENTACION.md).
Se conserva SA-01: panel Superadmin, Personas, Áreas y Cargos. Consulta también
[implementación de SA-01](docs/SA01_IMPLEMENTACION.md) y
[pruebas Postman](docs/POSTMAN_PRUEBAS.md). Las secciones históricas siguientes
describen las fases anteriores de construcción.

Base existente: Django 6.1, Django REST Framework, PostgreSQL y Angular 21.

## Backend

Desde la raíz, en PowerShell, utilizando el entorno virtual existente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

En una instalación nueva, crea primero el entorno con `python -m venv .venv`.
Copia `.env.example` a `.env` solamente si `.env` no existe:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Completa estas variables en el `.env` de la raíz:

| Variable | Contenido |
| --- | --- |
| `DJANGO_SECRET_KEY` | Clave aleatoria privada; no usar `change-me`. |
| `DJANGO_DEBUG` | `True` para desarrollo local; `False` fuera de desarrollo. |
| `POSTGRES_DB` | Nombre de la base PostgreSQL existente. |
| `POSTGRES_USER` | Usuario PostgreSQL. |
| `POSTGRES_PASSWORD` | Contraseña actual de ese usuario. |
| `POSTGRES_HOST` | Host del servidor; por defecto `localhost`. |
| `POSTGRES_PORT` | Puerto del servidor; por defecto `5432`. |

Si ya existe un `.env` local configurado, conserva sus valores privados;
no lo reemplaces con el archivo de ejemplo.

Django carga este archivo independientemente del directorio de ejecución.
Las variables del proceso tienen prioridad. Los valores se leen literalmente,
sin interpolar `${...}` en contraseñas. La configuración falla con un mensaje
explícito si falta una variable obligatoria o contiene `change-me`.
Si se omite `DJANGO_DEBUG`, se utiliza `False`.

```powershell
.\.venv\Scripts\python.exe backend/manage.py check
.\.venv\Scripts\python.exe backend/manage.py runserver
```

La base debe existir y el servicio PostgreSQL debe estar disponible.
Estos comandos no crean ni migran la base de datos. La configuración actual
de hosts se conserva para desarrollo local.

## Arquitectura del Backend

El backend utiliza una base de Arquitectura Hexagonal (Ports and Adapters).
SASPEL todavía no tiene módulos funcionales implementados. El único caso de
uso nuevo es una comprobación técnica de ejecución, sin lógica de negocio.

- **Domain:** entidades, objetos de valor, contratos de repositorio, servicios
  y excepciones de negocio. Es Python puro y no conoce Django, HTTP ni ORM.
- **Application:** casos de uso, DTOs, puertos y coordinación de aplicación.
  Puede importar Domain; no importa Django, DRF ni Infrastructure.
- **Infrastructure:** adaptadores HTTP, persistencia ORM, configuración de
  adaptadores y factorías de dependencias. Puede importar ambas capas internas.
- **Ports:** contratos definidos en el núcleo. Los puertos de entrada describen
  operaciones ofrecidas por los casos de uso; los de salida describen servicios
  externos que esos casos necesitan.
- **Adapters:** implementaciones externas que invocan puertos de entrada o
  implementan puertos de salida. Django y DRF quedan en esta capa.

La regla de dependencias del código es:

```text
Infrastructure ---> Application ---> Domain
       |                                ^
       +--------------------------------+
```

El núcleo no importa capas externas. Un futuro caso de uso dependerá del
contrato de salida, nunca de su implementación Django. El código de arranque
`backend/config/` permanece fuera del núcleo y conecta Django con Infrastructure.

Árbol simplificado (todos los paquetes incluyen `__init__.py`):

```text
backend/
|-- manage.py
|-- requirements.txt
|-- config/
|   |-- settings.py
|   |-- urls.py
|   |-- asgi.py
|   `-- wsgi.py
|-- src/
|   |-- domain/
|   |   |-- entities/
|   |   |-- value_objects/
|   |   |-- repositories/
|   |   |-- services/
|   |   `-- exceptions/
|   |-- application/
|   |   |-- dto/health.py
|   |   |-- ports/
|   |   |   |-- input/health.py
|   |   |   `-- output/
|   |   |-- use_cases/health.py
|   |   `-- services/
|   `-- infrastructure/
|       |-- persistence/django/
|       |   |-- apps.py
|       |   |-- models/
|       |   |-- migrations/
|       |   `-- repositories/
|       |-- api/rest/
|       |   |-- serializers/
|       |   |-- views/
|       |   |   |-- health.py
|       |   |   `-- prueba.py
|       |   `-- urls.py
|       |-- dependencies/health.py
|       `-- config/
`-- tests/
    |-- test_architecture.py
    |-- test_health_use_case.py
    `-- test_health_api.py
```

Responsabilidades de los paquetes preparados para futuras implementaciones:

| Paquete | Responsabilidad |
| --- | --- |
| `domain/entities` | Identidad y comportamiento de entidades Python, sin `models.Model`. |
| `domain/value_objects` | Valores inmutables e invariantes de negocio. |
| `domain/repositories` | Contratos de almacenamiento de entidades del dominio, sin ORM. |
| `domain/services` | Reglas de negocio que abarcan varias entidades o valores. |
| `domain/exceptions` | Errores de negocio sin códigos HTTP. |
| `application/ports/output` | Contratos para otros servicios externos requeridos por casos de uso. |
| `application/services` | Coordinación compartida entre casos de uso. |
| `persistence/django/models` | Representaciones ORM separadas de las entidades de dominio. |
| `persistence/django/migrations` | Evolución del esquema de la app técnica. |
| `persistence/django/repositories` | Implementaciones ORM de los contratos del núcleo. |
| `api/rest/serializers` | Validación y representación del transporte HTTP. |
| `infrastructure/config` | Configuración específica de futuros adaptadores; no duplica `backend/config`. |

Estos paquetes solo documentan su responsabilidad por ahora. No contienen
entidades, repositorios ni servicios ficticios. Los contratos de repositorio
del dominio no se duplicarán en `application/ports/output`.

El siguiente esquema distingue el flujo del ejemplo y las extensiones futuras:

```text
INPUT ADAPTER
REST / DRF
    |
    v
INPUT PORT: HealthCheck
    |
    v
APPLICATION: GetHealthStatus ------> DOMAIN (futuro)
    |
    +-- devuelve HealthResult (implementado)
    |
    v
OUTPUT PORT (futuro)
    ^
    | implementa
OUTPUT ADAPTER (futuro)
DJANGO REPOSITORY ------> POSTGRESQL
```

`GetHealthStatus` implementa el puerto `HealthCheck`, definido con
`typing.Protocol`. La factoría `build_health_check()` en
`infrastructure/dependencies` selecciona la implementación concreta.
La vista recibe el puerto mediante esa factoría, llama a `execute()` y
traduce el DTO `HealthResult` a JSON. No se utiliza una librería de inyección.
El ejemplo no necesita acceder a Domain, persistencia ni puertos de salida.
Tampoco necesita un serializer para validar entrada, porque no recibe datos.

La app técnica `PersistenceConfig` se registra explícitamente en
`INSTALLED_APPS`. Su ruta es `src.infrastructure.persistence.django`, pero
conserva la etiqueta anterior `api` para mantener la identidad de Django.
Los futuros modelos se definirán bajo `models/` y se importarán en su
`__init__.py` para que Django los descubra. No se han creado modelos ni
migraciones en esta fase.

La antigua app `backend/api` se retiró: sus archivos de modelos, admin y tests
eran plantillas vacías. Su vista de prueba se trasladó a Infrastructure y
`GET /api/` conserva la respuesta `{"mensaje": "Django funciona"}`.
El admin incorporado de Django conserva su configuración previa.
Los cachés locales `.pyc` de carpetas antiguas se ignoran y no forman parte
del código fuente publicado.

### Comprobación técnica y tests

Con Django en ejecución:

```powershell
curl.exe -i http://127.0.0.1:8000/api/health/
```

Respuesta HTTP 200, de tipo `application/json`:

```json
{"status": "ok", "architecture": "hexagonal"}
```

Este endpoint público solo demuestra que la aplicación puede ejecutar el caso
de uso y responder por DRF. No comprueba la disponibilidad de PostgreSQL ni
constituye una comprobación completa de dependencias externas.

Desde `backend`, ejecuta:

```powershell
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py test --verbosity 2
```

Las siete pruebas comprueban el resultado del caso de uso, el contrato HTTP,
la delegación al puerto, el rechazo de POST, la ruta anterior y los imports
de Domain y Application. Las pruebas HTTP usan `SimpleTestCase`, que impide
consultas a la base; la suite no crea ni modifica bases de datos.

También puedes ejecutar el núcleo y sus guardas arquitectónicas sin cargar
paquetes externos, Django ni `.env`:

```powershell
..\.venv\Scripts\python.exe -S -m unittest tests.test_health_use_case tests.test_architecture -v
```

Las guardas inspeccionan imports estáticos, incluidos los relativos. Permiten
la biblioteca estándar (salvo detalles explícitos de transporte/persistencia)
y las capas internas autorizadas; rechazan dependencias externas como Django,
DRF y psycopg. No son un analizador de imports dinámicos.

No se agregaron dependencias, hacks de `sys.path`, funcionalidades de SASPEL
ni cambios en Angular. El adaptador utiliza las APIs habituales de
[Django REST Framework](https://www.django-rest-framework.org/api-guide/views/).

## Modelo de datos inicial

Este es únicamente el primer bloque físico de la BD. Los cuatro modelos ORM
están en `backend/src/infrastructure/persistence/django/models/`, registrados
en la app `api`. Domain y Application continúan independientes de Django.

```text
auth_user
    | 1:1
    v
perfil_usuario
    |-- area_institucional (N:1, opcional)
    `-- cargo_institucional (N:1, opcional)

auth_user (trabajador) --1:N--> asignacion_profesional <--N:1-- auth_user (psicologo)
```

Las cuatro tablas propias llevan el prefijo `saspel_`. Se reutiliza el usuario
de Django mediante `settings.AUTH_USER_MODEL`, sin duplicar sus datos de
identidad o autenticación. Los roles son Django Groups: `NUEVO_TRABAJADOR`,
`TRABAJADOR`, `PSICOLOGO`, `ADMIN` y `SUPERADMIN`; este último identifica el rol
funcional, mientras `is_superuser` permite privilegios técnicos por separado.
La migración `api.0002_crear_roles_iniciales` usa `get_or_create`, no crea usuarios
ni asigna permisos y conserva los grupos al revertir para proteger membresías.

La BD impide autoasignaciones, estados fuera del catálogo y más de una
asignación `ACTIVA` por trabajador, permitiendo historial `FINALIZADA` y
`REASIGNADA`. El ORM protege con `PROTECT` los usuarios referenciados por
asignaciones y las áreas/cargos en uso. El perfil usa `CASCADE` respecto al
usuario. `habilitado_asignaciones` permite pausar nuevas asignaciones sin
desactivar al usuario; todavía no se implementa reparto automático.

Los modelos tienen registro básico en Django Admin. Este bloque no agrega
endpoints, casos de uso funcionales ni cambios de frontend. Las descripciones
de paquetes vacíos y siete pruebas anteriores corresponden a la fase previa:
la suite ahora incluye pruebas de integridad sobre una BD PostgreSQL de pruebas
separada, creada y eliminada por Django (el usuario de pruebas necesita `CREATEDB`).

Desde `backend`, usando el entorno virtual existente:

```powershell
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py sqlmigrate api 0001_initial
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py test --noinput --verbosity 2
..\.venv\Scripts\python.exe -m pip check
```

## Modelo de instrumentos psicológicos

BD-03 agrega exclusivamente nueve tablas físicas bajo el prefijo `saspel_`,
mediante `api.0003_instrumentos_psicologicos`. Los modelos permanecen en
`backend/src/infrastructure/persistence/django/models/`, con registro básico
en Django Admin y sin dependencias de Django en Domain/Application.

```text
Instrumento (codigo + version)
    |-- Preguntas
    |     `-- Escala (opcional)
    |            `-- Opciones
    |-- Rangos
    `-- Asignaciones <-- auth_user (trabajador / asignado_por opcional)
             | 1:0..1
             v
          Aplicación
           |-- Respuestas --> Pregunta / Opción (opcional)
           `-- Resultado (0..1) --> Rango (opcional)
```

La normalización usa valores atómicos y ninguna lista en columnas (1FN);
los atributos describen su registro completo y las combinaciones únicas
evitan duplicados dentro de su instrumento, escala o aplicación (2FN).
Aplicaciones, respuestas y resultados obtienen trabajador e instrumento
por `aplicacion -> asignacion`; el resultado obtiene el nombre y la
interpretación mediante su rango, sin copiar datos transitivos (3FN).
`puntaje_total` se persiste explícitamente en el resultado; no se calcula aquí.

`(codigo, version)` identifica cada versión. Se permiten asignaciones repetidas
del mismo instrumento a un trabajador, con hasta una aplicación por asignación
y un resultado por aplicación. Cada pregunta admite una respuesta por aplicación.
Las relaciones usan `PROTECT` para evitar borrar registros referenciados desde
el ORM; las claves foráneas tampoco tienen borrado SQL en cascada. Las nuevas
versiones deben crearse en registros separados: la inmutabilidad de versiones
aplicadas y el caso de uso de versionado quedan para una fase posterior.

La BD valida unicidades, los catálogos de tipos/estados/origen, órdenes no
negativos y `puntaje_minimo <= puntaje_maximo`. Las escalas de preguntas son
opcionales. La coherencia entre instrumento, pregunta, opción y rango, los
tipos de valores respondidos y los solapamientos se validarán posteriormente
en Application. Se utiliza `DecimalField(max_digits=12, decimal_places=4)`
para valores numéricos y puntajes. El origen se indica explícitamente; los
estados iniciales son `PENDIENTE` para asignaciones e `INICIADA` para aplicaciones.

No se insertan instrumentos, preguntas, escalas ni rangos reales. Las pruebas
usan datos ficticios en una BD PostgreSQL temporal. Este bloque no implementa
puntuación, interpretación automática, endpoints, casos de uso ni frontend.

Desde `backend`, para revisar y verificar este bloque:

```powershell
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py sqlmigrate api 0003_instrumentos_psicologicos
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py test --noinput --verbosity 2
..\.venv\Scripts\python.exe -m pip check
```

## Modelo de Citas y Disponibilidad

BD-04 añade `saspel_disponibilidad_psicologo` y `saspel_cita` mediante la
migración incremental `api.0004_citas_disponibilidad`. Los modelos ORM siguen
en Infrastructure y el admin solo los registra para inspección de desarrollo.

```text
Psicólogo (auth_user)
   |-- Disponibilidad semanal
   `-- Cita <-- Trabajador (auth_user)
         ^
         `-- solicitada_por (auth_user)

Reprogramación futura:
Cita original [REPROGRAMADA]
     ^
     | cita_origen
Nueva cita [SOLICITADA]
     ^
     | cita_origen
Otra reprogramación
```

Solicitud y cita son una sola tabla: `SOLICITADA` identifica la solicitud
inicial. Los otros estados son `CONFIRMADA`, `COMPLETADA`, `CANCELADA`,
`RECHAZADA` y `REPROGRAMADA`; prioridad admite `BAJA`, `MEDIA` y `ALTA`.
`motivo_cierre` registra razones administrativas, mientras las notas
profesionales pertenecerán al futuro seguimiento. No se implementan aún
transiciones de estado ni el caso de uso de reprogramación: este creará otra
fila con `cita_origen`, conservando las fechas anteriores. Las FK usan `PROTECT`
para preservar los usuarios y antecedentes referenciados.

La disponibilidad es recurrente: lunes=0 hasta domingo=6, con horas locales de
la zona institucional `America/La_Paz`. No incluye vacaciones, feriados ni
excepciones. La BD exige inicio anterior al fin, día válido y unicidad exacta
del bloque por psicólogo, día y horas. Las citas exigen fechas crecientes,
participantes diferentes, estados/prioridades válidos y ausencia de referencia
directa a sí mismas. Los ciclos de varias citas se validarán en Application.

Los índices `(psicologo, dia_semana, activo)`,
`(psicologo, fecha_inicio, estado)` y `(trabajador, fecha_inicio, estado)`
preparan consultas de agenda y cubren sus FK iniciales sin índices simples
redundantes. No impiden solapamientos: Application validará conflictos de ambos
participantes, disponibilidad, grupos y autorización profesional. No se agrega
una FK a `AsignacionProfesional`; esa relación se verificará cuando la regla
funcional lo requiera. Tampoco se añaden exclusiones SQL ni librerías nuevas.

**Normalización:** valores atómicos y sin listas (1FN); los atributos describen
el registro completo identificado por su PK (2FN); identidades y perfiles se
obtienen mediante FK y no se almacenan duración ni día calculado en Cita (3FN).
En disponibilidad, el día es parte de la recurrencia, no derivado de una fecha.

Los modelos, migraciones y pruebas de persistencia de BD-01 a BD-04 documentan
las decisiones de relaciones, restricciones e historial. La documentación de
los bloques anteriores no cambia campos, operaciones ni comportamiento.
Las pruebas usan una base PostgreSQL temporal; las dos tablas nuevas quedan
vacías en la base principal. No se implementan endpoints, serializers, frontend
ni casos de uso funcionales en esta fase.

Desde `backend`:

```powershell
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py sqlmigrate api 0004_citas_disponibilidad
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py test --noinput --verbosity 2
..\.venv\Scripts\python.exe -m pip check
..\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

## Primer acceso funcional: bienvenida, login y panel por rol

La primera rebanada funcional permite visitar la bienvenida, iniciar sesión
con correo y contraseña y entrar al panel inicial del rol. Los textos de fases
anteriores sobre ausencia de casos de uso describen aquellas etapas: ahora
existen `AuthenticateUser` y `GetAuthenticatedUser`, independientes de Django.

El backend ofrece `POST /api/auth/login/`, `GET /api/auth/me/` y
`POST /api/auth/refresh/`. Se fijaron `djangorestframework-simplejwt==5.5.1` y
`PyJWT==2.13.0`; no se activó blacklist ni se añadieron tablas o migraciones.
Los roles proceden de Django Groups, con prioridad SUPERADMIN, ADMIN,
PSICOLOGO, TRABAJADOR y NUEVO_TRABAJADOR. Un superusuario técnico se considera
SUPERADMIN; una cuenta sin rol se rechaza. Los correos se buscan sin distinguir
mayúsculas y se rechazan coincidencias ambiguas.

Angular se organiza en `core/auth`, `features/welcome`, `features/auth/login`,
`features/dashboards` y `shared/brand`. Login y panel utilizan ViewModels; las
cinco rutas de panel comparten una vista inicial sin módulos internos. Los guards
recuperan la identidad desde `/me`; los tokens viven en `sessionStorage` y el
interceptor gestiona una renovación compartida con un solo reintento.

Configura en el `.env` local ignorado las variables `SASPEL_DEV_SUPERADMIN_EMAIL`
y `SASPEL_DEV_SUPERADMIN_PASSWORD`. El comando explícito
`python manage.py bootstrap_dev_superadmin`, ejecutado desde `backend` con el
entorno virtual, crea o actualiza la cuenta solo con `DEBUG=True`; usa la
contraseña de ese archivo y asegura el grupo SUPERADMIN y los indicadores de
cuenta activa, staff y superusuario. No crea perfiles ni cuentas demo adicionales.
El archivo `.env.example` mantiene ambos valores vacíos.

Consulta [la guía de Postman](docs/POSTMAN_PRUEBAS.md) para URLs, cuerpos,
respuestas, errores y preparación local. El [informe de esta fase](docs/AUTH_IMPLEMENTACION.md)
registra los archivos y las verificaciones. Logout es local y no revoca tokens
en el servidor; ese refuerzo queda para una etapa posterior.

## Frontend

Desde `frontend`:

```powershell
npm.cmd ci
npm.cmd run build
npm.cmd start
```

Si `node_modules` ya está instalado, no es necesario ejecutar `npm.cmd ci`
para iniciar o compilar.

## Git y secretos

El `.gitignore` raíz excluye entornos virtuales, dependencias, cachés, archivos
de IDE, SQLite y archivos `.env`; permite versionar `.env.example`.
El remoto `origin` corresponde al
[repositorio SASPEL](https://github.com/Arenazcruz/SASPEL---Sistema-de-Ayuda-Segimiento-Prevencion-del-Estres-Laboral).
El flujo recomendado es `feature/*` → PR a `develop` → pruebas → PR a `main`.
No desarrollar nuevas funcionalidades directamente en `main`.
Consulta [docs/ESTRATEGIA_GIT.md](docs/ESTRATEGIA_GIT.md) para el procedimiento.

También se excluyen logs, archivos temporales, dumps SQL, bases SQLite y
archivos comprimidos. Las capturas locales de SA-01 y su runner Python
contienen referencias a una cuenta personal y se conservan solo localmente.

## Rotación manual opcional de la contraseña PostgreSQL

La limpieza no cambia la contraseña del servidor. Si la contraseña anterior
se compartió o publicó, conviene rotarla. En esta máquina, PostgreSQL 18 está
instalado fuera del `PATH`; desde la raíz, en PowerShell:

```powershell
$env:Path = 'C:\Program Files\PostgreSQL\18\bin;' + $env:Path
.\.venv\Scripts\python.exe backend/manage.py dbshell
```

Dentro de `psql`, ejecuta:

```text
\password
\q
```

`\password` solicita la nueva contraseña del usuario conectado de forma
interactiva. Actualiza después `POSTGRES_PASSWORD` en `.env` con exactamente
esa contraseña y reinicia Django. Actualiza también cualquier otra aplicación
local que use ese mismo usuario. Documentación:
[psql: comando de contraseña](https://www.postgresql.org/docs/current/app-psql.html).
