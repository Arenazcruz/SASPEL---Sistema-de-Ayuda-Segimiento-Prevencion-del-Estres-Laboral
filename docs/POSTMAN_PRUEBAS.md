# Pruebas rápidas de SASPEL en Postman

**BACKEND:** http://127.0.0.1:8000  
**FRONTEND:** http://localhost:4200

En Postman crea variables locales `superadmin_email`, `superadmin_password`,
`access_token` y `refresh_token`. Obtén el correo de `SASPEL_DEV_SUPERADMIN_EMAIL`
y `superadmin_password` de `SASPEL_DEV_SUPERADMIN_PASSWORD`
en el `.env` local. Mantén este valor privado; no lo incluyas en colecciones
exportadas o compartidas. La contraseña real no se documenta aquí.

## 1. Health

- Método: **GET**
- URL: **http://127.0.0.1:8000/api/health/**
- Headers: `Accept: application/json`
- Autorización: **No Auth**.
- Body: ninguno.
- Respuesta: **200 OK**.

```json
{"status": "ok", "architecture": "hexagonal"}
```

Comprueba que Django responde; no comprueba por sí mismo PostgreSQL.
Un método no permitido devuelve **405**. Si no se puede conectar, comprueba
que el servidor esté levantado en el puerto 8000.

## 2. Login por correo

- Método: **POST**
- URL: **http://127.0.0.1:8000/api/auth/login/**
- Headers: `Content-Type: application/json`, `Accept: application/json`
- Autorización: **No Auth**. No enviar un Bearer anterior.
- Body: **raw / JSON**.

```json
{
  "email": "{{superadmin_email}}",
  "password": "{{superadmin_password}}"
}
```

Respuesta **200 OK** (el id depende de la cuenta existente):

```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>",
  "user": {
    "id": 1,
    "email": "superadmin@example.com",
    "first_name": "",
    "last_name": "",
    "role": "SUPERADMIN"
  },
  "dashboard_path": "/dashboard/superadmin"
}
```

Copia los tokens en las variables locales `access_token` y `refresh_token`.
También puedes guardar esta acción en **Scripts → Post-response**:

```javascript
if (pm.response.code === 200) {
  const session = pm.response.json();
  pm.environment.set('access_token', session.access);
  pm.environment.set('refresh_token', session.refresh);
}
```

Errores principales:

| Estado | Situación |
| --- | --- |
| 400 | Correo con formato incorrecto, contraseña vacía o datos requeridos ausentes. |
| 401 | Correo o contraseña incorrectos; también correo ambiguo entre varias cuentas. |
| 403 | Cuenta inactiva con contraseña correcta, o cuenta sin rol funcional. |
| 405 | Método diferente de POST. |

Correo inexistente y contraseña incorrecta reciben el mismo mensaje:

```json
{"detail": "Correo o contraseña incorrectos."}
```

La búsqueda del correo no distingue mayúsculas. Solo después de verificar la
contraseña se distingue una cuenta inactiva; una clave incorrecta sigue dando 401.
Los usuarios creados por SASPEL utilizan el correo como `username` y `email`.

## 3. Consultar la cuenta autenticada

- Método: **GET**
- URL: **http://127.0.0.1:8000/api/auth/me/**
- Headers: `Accept: application/json`, `Authorization: Bearer {{access_token}}`
- Body: ninguno.
- Respuesta: **200 OK**.

```json
{
  "id": 1,
  "email": "superadmin@example.com",
  "first_name": "",
  "last_name": "",
  "role": "SUPERADMIN",
  "dashboard_path": "/dashboard/superadmin"
}
```

El rol se consulta de nuevo en Django: no se toma de un valor guardado por el
navegador ni de una clasificación antigua dentro del token.

- **401:** falta el access, expiró, fue alterado o la cuenta ya no puede autenticarse.
- **403:** la cuenta ya no tiene un rol funcional de acceso.
- **405:** método diferente de GET.

## 4. Renovar el access

- Método: **POST**
- URL: **http://127.0.0.1:8000/api/auth/refresh/**
- Headers: `Content-Type: application/json`, `Accept: application/json`
- Autorización: **No Auth**.
- Body: **raw / JSON**.

```json
{"refresh": "{{refresh_token}}"}
```

Respuesta **200 OK**:

```json
{"access": "<nuevo_access_token>"}
```

Reemplaza `access_token` con el nuevo valor y vuelve a probar `/me`.
El refresh permanece igual: esta fase no utiliza rotación ni blacklist.

- **400:** falta el campo refresh o su formato no es válido.
- **401:** token inválido, expirado, de tipo incorrecto, o cuenta borrada/inactiva.
- **405:** método diferente de POST.

El access dura **5 minutos** y el refresh **1 día**. No compartas tokens ni los
incluyas en documentación o capturas. Las respuestas de sesión usan `no-store`.

## Flujo de prueba rápido

1. Ejecuta **health** y confirma 200.
2. Ejecuta **login** con la variable de contraseña local.
3. Copia `access` y `refresh` en sus variables locales.
4. Ejecuta **/me** y comprueba rol y panel.
5. Ejecuta **refresh**, actualiza `access_token` y repite **/me**.

## Redirección por rol

| Rol | Ruta Angular |
| --- | --- |
| NUEVO_TRABAJADOR | `/dashboard/nuevo-trabajador` |
| TRABAJADOR | `/dashboard/trabajador` |
| PSICOLOGO | `/dashboard/psicologo` |
| ADMIN | `/dashboard/admin` |
| SUPERADMIN | `/dashboard/superadmin` |

Si existen varios grupos, se utiliza esta prioridad:
**SUPERADMIN → ADMIN → PSICOLOGO → TRABAJADOR → NUEVO_TRABAJADOR**.
`is_superuser=True` se interpreta como SUPERADMIN. El comando local asegura
también su pertenencia al grupo SUPERADMIN. El módulo SA-01 crea cuentas con
un único rol funcional; login y `/me` no modifican los grupos.

## Preparar y ejecutar el entorno

Desde `backend`, con las variables locales ya configuradas:

```powershell
..\.venv\Scripts\python.exe manage.py bootstrap_dev_superadmin
..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

El comando de bootstrap solo funciona con `DEBUG=True`, no muestra la
contraseña y crea o actualiza la misma cuenta sin duplicarla. Lee los valores
de `SASPEL_DEV_SUPERADMIN_EMAIL` y `SASPEL_DEV_SUPERADMIN_PASSWORD`.

Desde otra terminal, en `frontend`:

```powershell
npm.cmd start
```

Angular permite visitar `/` públicamente. En `/login` se introducen las
credenciales; tras ingresar se muestra el panel del rol. Al recargar o cambiar
de panel se consulta `/me`. Una sesión ya iniciada que visite `/login` vuelve
a su panel. Un rol no puede abrir el panel de otro escribiendo la URL.

Angular guarda únicamente los dos tokens en **sessionStorage**. Ante un 401
renueva una sola vez y reintenta la solicitud; las peticiones simultáneas
comparten la renovación. Si falla, limpia la sesión y vuelve a `/login`.
Nunca envía el Bearer a otros servidores ni al login o refresh.

**Cerrar sesión** borra tokens y estado local; no existe endpoint de logout
ni revocación del refresh en servidor en esta fase. Un token copiado podría
seguir vigente hasta su vencimiento. La revocación/blacklist y otras medidas
de producción se abordarán posteriormente.

Los orígenes CORS locales son `http://localhost:4200` y `http://127.0.0.1:4200`,
configurables mediante `DJANGO_CORS_ALLOWED_ORIGINS` (lista separada por comas).
`DJANGO_ALLOWED_HOSTS` configura los hosts de Django. No se habilita CORS global.
El build de producción de Angular usa `/api` en su mismo origen; el servidor
de publicación deberá dirigir ese prefijo a Django.

## Referencias de implementación

Se utiliza [SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/getting_started.html)
para emitir tokens y su [configuración de vigencia](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html).
Angular conecta el acceso mediante [interceptores HTTP](https://angular.dev/guide/http/interceptors)
y [guards de rutas](https://angular.dev/guide/routing/route-guards).

## SUPERADMIN - PERSONAS

SA-01 utiliza los registros existentes de cuentas, perfiles, grupos, áreas y cargos.
Todos los endpoints siguientes requieren usuario activo y **grupo funcional
SUPERADMIN**, además de un JWT válido. Los flags técnicos por sí solos no
permiten administrar este módulo. ADMIN y TRABAJADOR reciben 403; sin JWT, 401.

Variables adicionales del entorno Postman:

| Variable | Uso |
| --- | --- |
| `base_url` | Origen del backend, por ejemplo `http://127.0.0.1:8000` (sin `/api`). |
| `superadmin_access` | Access token obtenido con el login del Superadmin. |
| `test_user_email` | Correo único de la persona de prueba. |
| `test_user_password` | Clave de prueba definida localmente; no guardar en documentación. |
| `test_user_new_password` | Nueva clave para comprobar el restablecimiento. |
| `test_user_id` | ID devuelto al registrar la persona. |
| `test_employee_code` | Código de empleado único. |
| `area_id`, `cargo_id` | IDs de opciones institucionales activas. |

En estas solicitudes usar `Authorization: Bearer {{superadmin_access}}` y
`Content-Type: application/json`. Las claves requieren al menos 8 caracteres,
una letra y un número; también se aplican los validadores de Django.

### Resumen y listado

```http
GET {{base_url}}/api/superadmin/dashboard/summary/
GET {{base_url}}/api/superadmin/users/
GET {{base_url}}/api/superadmin/users/?role=NUEVO_TRABAJADOR&active=true&page=1
GET {{base_url}}/api/superadmin/users/?search={{test_employee_code}}&area={{area_id}}&cargo={{cargo_id}}
```

El resumen calcula `users_total`, `new_workers`, `workers`, `psychologists`,
`admins`, `superadmins`, `active_users`, `inactive_users` y `recent_users`
(los últimos cinco) desde PostgreSQL. No se guardan estadísticas en tablas.

Listado: `search` busca correo, nombres, apellido paterno y código;
`role`, `active=true|false`, `area`, `cargo` son opcionales. Omitir `active`
incluye ambos estados. `page` empieza en 1; las páginas contienen hasta 20 filas.

Estructura de paginación:

```json
{
  "count": 0,
  "page": 1,
  "page_size": 20,
  "results": []
}
```

Cada persona contiene `id`, nombres, `nombre_completo`, correo, `role`,
`codigo_empleado`, `area`, `cargo`, `is_active`, `tamizaje_resuelto`,
`habilitado_asignaciones`, `fecha_registro`, `last_login` y `tiene_perfil`.
Área/cargo son objetos `{id, nombre, descripcion, activo}` o `null`.
Una cuenta antigua sin perfil sigue apareciendo, con campos personales vacíos.

### Registrar persona

```http
POST {{base_url}}/api/superadmin/users/
```

```json
{
  "email": "{{test_user_email}}",
  "password": "{{test_user_password}}",
  "password_confirmation": "{{test_user_password}}",
  "first_name": "Persona",
  "last_name": "Prueba",
  "apellido_materno": "Temporal",
  "codigo_empleado": "{{test_employee_code}}",
  "nombre_preferido": "",
  "fecha_nacimiento": null,
  "sexo": "",
  "telefono": "",
  "area_id": {{area_id}},
  "cargo_id": {{cargo_id}},
  "role": "NUEVO_TRABAJADOR"
}
```

Respuesta 201: la persona creada, sin contraseña ni hash. Copiar `id` a
`test_user_id`. Opcionalmente, usar en **Tests / Post-response**:

```javascript
pm.test('Persona registrada', () => pm.response.to.have.status(201));
pm.environment.set('test_user_id', pm.response.json().id);
```

El correo se normaliza; correo y username quedan sincronizados. Se rechazan
duplicados de correo sin distinguir mayúsculas y códigos de empleado repetidos.
Cuenta, perfil y grupo se crean en una sola transacción.

Roles de creación: `NUEVO_TRABAJADOR`, `PSICOLOGO`, `ADMIN`, `SUPERADMIN`.
`TRABAJADOR` devuelve 400. Para PSICOLOGO puede agregarse
`"habilitado_asignaciones": true` (valor predeterminado). Solo SUPERADMIN
recibe `is_staff=True` e `is_superuser=True`.

### Consultar y editar

```http
GET {{base_url}}/api/superadmin/users/{{test_user_id}}/
PATCH {{base_url}}/api/superadmin/users/{{test_user_id}}/
```

Ejemplo de PATCH:

```json
{
  "email": "{{test_user_email}}",
  "first_name": "Persona editada",
  "apellido_materno": "Temporal",
  "nombre_preferido": "Prueba",
  "telefono": "+591 70000000",
  "area_id": {{area_id}},
  "cargo_id": {{cargo_id}}
}
```

También admite `last_name`, `codigo_empleado`, `fecha_nacimiento`, `sexo`
(`F`, `M`, `O` o vacío). Los vínculos institucionales pueden vaciarse con
`null`. Se conservan vínculos históricos inactivos, pero las nuevas selecciones
deben estar activas. `habilitado_asignaciones` solo se edita para PSICOLOGO.
Para completar una cuenta sin perfil hay que proporcionar `codigo_empleado`.

PATCH rechaza `password`, `role`, `is_active`, `is_superuser`,
`tamizaje_resuelto` y cualquier campo no previsto (400).

### Activar y desactivar

```http
POST {{base_url}}/api/superadmin/users/{{test_user_id}}/deactivate/
POST {{base_url}}/api/superadmin/users/{{test_user_id}}/activate/
```

Body `{}`; respuesta 200 con el estado actualizado. Se conserva el perfil y el
historial. `DELETE` no está publicado y responde 405. El backend rechaza
desactivarse a sí mismo y dejar el sistema sin un SUPERADMIN activo.

### Restablecer contraseña

```http
POST {{base_url}}/api/superadmin/users/{{test_user_id}}/reset-password/
```

```json
{
  "password": "{{test_user_new_password}}",
  "password_confirmation": "{{test_user_new_password}}"
}
```

Respuesta 200: `{"detail": "Contraseña restablecida."}`. El login con la
clave anterior debe devolver 401 y el login con la nueva debe funcionar.
No se devuelve ni se registra la contraseña.

### Cambiar rol administrativo

```http
POST {{base_url}}/api/superadmin/users/{{test_user_id}}/role/
```

```json
{
  "role": "ADMIN"
}
```

Reglas explícitas: una cuenta con perfil y rol actual PSICOLOGO, ADMIN o
SUPERADMIN puede corregirse a NUEVO_TRABAJADOR, PSICOLOGO, ADMIN o SUPERADMIN.
No hay cambios desde roles de trabajador ni hacia TRABAJADOR en este módulo.
Enviar el mismo rol no altera datos. Un Superadmin no puede quitarse su propio
rol ni quitar el del último activo. Las modificaciones y su validación se
serializan en una transacción. Al asignar NUEVO_TRABAJADOR el tamizaje vuelve
a `false`; PSICOLOGO queda habilitado para asignaciones.

### Áreas y cargos

```http
GET {{base_url}}/api/superadmin/areas/
GET {{base_url}}/api/superadmin/areas/?active=true
POST {{base_url}}/api/superadmin/areas/
GET {{base_url}}/api/superadmin/areas/{{area_id}}/
PATCH {{base_url}}/api/superadmin/areas/{{area_id}}/
POST {{base_url}}/api/superadmin/areas/{{area_id}}/deactivate/
POST {{base_url}}/api/superadmin/areas/{{area_id}}/activate/

GET {{base_url}}/api/superadmin/cargos/
GET {{base_url}}/api/superadmin/cargos/?active=true
POST {{base_url}}/api/superadmin/cargos/
GET {{base_url}}/api/superadmin/cargos/{{cargo_id}}/
PATCH {{base_url}}/api/superadmin/cargos/{{cargo_id}}/
POST {{base_url}}/api/superadmin/cargos/{{cargo_id}}/deactivate/
POST {{base_url}}/api/superadmin/cargos/{{cargo_id}}/activate/
```

Body de creación/edición:

```json
{
  "nombre": "Opción institucional de prueba",
  "descripcion": "Descripción temporal"
}
```

POST crea activo y devuelve 201; PATCH permite campos parciales y devuelve 200.
Listados devuelven un array sin paginación. Activar/desactivar usa `{}` y el
campo existente `activo`. No hay eliminación física ni nuevas tablas.

### Flujo de prueba completo

1. Login Superadmin en `POST {{base_url}}/api/auth/login/` con sus credenciales locales.
2. Copiar `access` a `superadmin_access`.
3. Crear o seleccionar área y cargo activos; registrar un NUEVO_TRABAJADOR con datos únicos.
4. Consultarlo por ID y comprobar perfil, rol y vínculos institucionales.
5. Editar sus datos y volver a consultarlos.
6. Cerrar sesión de Angular en `http://localhost:4200`.
7. Iniciar sesión con `test_user_email` y `test_user_password`.
8. Verificar rol NUEVO_TRABAJADOR y `/dashboard/nuevo-trabajador`. Postman verifica
   `dashboard_path`; la navegación se comprueba en Angular.
9. Cerrar sesión del trabajador y volver a ingresar como Superadmin.
10. Desactivar al usuario creado.
11. Intentar login con las credenciales correctas del trabajador.
12. Debe fallar con 403 y no emitir tokens.
13. Reactivarlo desde la cuenta Superadmin.
14. El login del trabajador vuelve a funcionar y conserva su perfil.

Comprobar también 403 con JWT de ADMIN/TRABAJADOR contra `/api/superadmin/users/`,
correo duplicado en mayúsculas, contraseña inválida y auto-desactivación rechazada.
Los registros reales se desactivan. La limpieza física solo corresponde a datos
locales puramente temporales y sin historial; nunca se ofrece desde esta API.
