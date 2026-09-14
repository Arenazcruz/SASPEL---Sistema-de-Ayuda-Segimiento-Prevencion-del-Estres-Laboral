// Prueba de navegador local. Recibe secretos solo por entorno y nunca los imprime.
// Ejecutar mediante sa01-local-check.py, que también verifica y limpia PostgreSQL.
const { chromium } = require(process.env.SA01_PLAYWRIGHT_MODULE);
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({channel: 'msedge', headless: true});
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('dialog', dialog => dialog.accept());
  const base = 'http://localhost:4200';
  const adminEmail = process.env.SASPEL_DEV_SUPERADMIN_EMAIL;
  const adminPassword = process.env.SASPEL_DEV_SUPERADMIN_PASSWORD;
  const email = process.env.SA01_TEST_EMAIL;
  const password = process.env.SA01_TEST_PASSWORD;
  const suffix = process.env.SA01_TEST_SUFFIX;
  const results = [];
  // Usa credenciales recibidas por entorno y espera el panel; registra solo la ruta.
  async function login(mail, secret, path) {
    await page.goto(base + '/login');
    await page.locator('#email').fill(mail);
    await page.locator('#password').fill(secret);
    await page.getByRole('button', {name: 'Ingresar', exact: false}).click();
    await page.waitForURL(base + path);
    results.push('Login y redirección: ' + path);
  }
  // Cierra la sesión desde la UI y espera login antes de probar otra cuenta.
  async function logout() {
    await page.getByRole('button', {name: /Cerrar sesión/}).click();
    await page.waitForURL(base + '/login');
  }
  try {
    await login(adminEmail, adminPassword, '/dashboard/superadmin');
    await page.getByText('Usuarios registrados recientemente', {exact: true}).waitFor();
    const summary = await page.evaluate(async () => {
      const response = await fetch('http://127.0.0.1:8000/api/superadmin/dashboard/summary/', {headers: {Authorization: 'Bearer ' + sessionStorage.getItem('saspel.access')}});
      return response.json();
    });
    assert(summary.users_total >= 1);
    results.push('Dashboard obtiene estadísticas reales.');
    // Crea catálogos temporales desde la interfaz para verificar también sus CRUD.
    for (const [kind, label] of [['areas', 'Áreas'], ['cargos', 'Cargos']]) {
      await page.getByRole('link', {name: label, exact: true}).click();
      await page.waitForURL(base + '/dashboard/superadmin/institucion/' + kind);
      await page.locator('[formcontrolname="nombre"]').fill('SA01-' + kind + '-' + suffix);
      await page.locator('[formcontrolname="descripcion"]').fill('Registro temporal de verificación SA-01');
      await page.getByRole('button', {name: 'Guardar', exact: true}).click();
      await page.getByRole('cell', {name: 'SA01-' + kind + '-' + suffix, exact: true}).waitFor();
      results.push('Catálogo creado mediante UI: ' + kind);
    }
    await page.getByRole('link', {name: 'Usuarios', exact: true}).click();
    await page.getByRole('link', {name: 'Registrar persona', exact: true}).click();
    await page.locator('[formcontrolname="email"]').fill(email);
    await page.locator('[formcontrolname="password"]').fill(password);
    await page.locator('[formcontrolname="password_confirmation"]').fill(password);
    await page.locator('[formcontrolname="codigo_empleado"]').fill('SA01-' + suffix);
    await page.locator('[formcontrolname="first_name"]').fill('Prueba');
    await page.locator('[formcontrolname="last_name"]').fill('Temporal');
    await page.locator('[formcontrolname="apellido_materno"]').fill('SA01');
    await page.locator('[formcontrolname="area_id"]').selectOption({label: 'SA01-areas-' + suffix});
    await page.locator('[formcontrolname="cargo_id"]').selectOption({label: 'SA01-cargos-' + suffix});
    await page.getByRole('button', {name: 'Registrar persona', exact: true}).click();
    await page.waitForURL(/\/dashboard\/superadmin\/personas\/\d+\?saved=created$/);
    const userId = Number(new URL(page.url()).pathname.split('/').at(-1));
    results.push('Nuevo trabajador registrado desde el formulario con área y cargo.');
    await page.getByRole('link', {name: 'Editar persona', exact: true}).click();
    await page.locator('[formcontrolname="telefono"]').fill('+591 70000000');
    await page.getByRole('button', {name: 'Guardar cambios', exact: true}).click();
    await page.waitForURL(/saved=updated/);
    await page.getByText('+591 70000000', {exact: true}).waitFor();
    results.push('Edición de persona verificada.');
    // Comprueba el registro persistido antes de cerrar la sesión administrativa.
    const record = await page.evaluate(async id => {
      const response = await fetch(`http://127.0.0.1:8000/api/superadmin/users/${id}/`, {headers: {Authorization: 'Bearer ' + sessionStorage.getItem('saspel.access')}});
      return response.json();
    }, userId);
    assert.equal(record.role, 'NUEVO_TRABAJADOR'); assert.equal(record.tiene_perfil, true);
    assert.equal(record.area.nombre, 'SA01-areas-' + suffix); assert.equal(record.cargo.nombre, 'SA01-cargos-' + suffix);
    assert(!('password' in record));
    await logout();
    await login(email, password, '/dashboard/nuevo-trabajador');
    await page.getByRole('heading', {name: 'Panel de bienvenida del nuevo trabajador'}).waitFor();
    // El mismo token de trabajador recibe 403 del servidor y el guard redirige la URL.
    const denied = await page.evaluate(async () => (await fetch('http://127.0.0.1:8000/api/superadmin/users/', {headers: {Authorization: 'Bearer ' + sessionStorage.getItem('saspel.access')}})).status);
    assert.equal(denied, 403);
    await page.goto(base + '/dashboard/superadmin/personas');
    await page.waitForURL(base + '/dashboard/nuevo-trabajador');
    results.push('Acceso ajeno rechazado por backend (403) y guard Angular.');
    await logout();
    await login(adminEmail, adminPassword, '/dashboard/superadmin');
    await page.goto(base + '/dashboard/superadmin/personas/' + userId);
    await page.getByRole('button', {name: 'Desactivar usuario', exact: true}).click();
    await page.getByRole('button', {name: 'Activar usuario', exact: true}).waitFor();
    await logout();
    await page.locator('#email').fill(email); await page.locator('#password').fill(password);
    await page.getByRole('button', {name: 'Ingresar', exact: false}).click();
    await page.getByRole('alert').filter({hasText: 'no está habilitada'}).waitFor();
    assert.equal(new URL(page.url()).pathname, '/login');
    results.push('Cuenta desactivada: login bloqueado.');
    await login(adminEmail, adminPassword, '/dashboard/superadmin');
    await page.goto(base + '/dashboard/superadmin/personas/' + userId);
    await page.getByRole('button', {name: 'Activar usuario', exact: true}).click();
    await page.getByRole('button', {name: 'Desactivar usuario', exact: true}).waitFor();
    await logout();
    await login(email, password, '/dashboard/nuevo-trabajador');
    results.push('Reactivación: login restaurado.');
    await logout();
    await login(adminEmail, adminPassword, '/dashboard/superadmin');
    await page.goto(base + '/dashboard/superadmin/personas/' + userId + '/password');
    const replacement = password + 'R2';
    await page.locator('[formcontrolname="password"]').fill(replacement);
    await page.locator('[formcontrolname="password_confirmation"]').fill(replacement);
    await page.getByRole('button', {name: 'Mostrar contraseñas', exact: true}).click();
    assert.equal(await page.locator('[formcontrolname="password"]').getAttribute('type'), 'text');
    await page.getByRole('button', {name: 'Restablecer contraseña', exact: true}).click();
    await page.getByRole('status').filter({hasText: 'correctamente'}).waitFor();
    assert.equal(await page.locator('[formcontrolname="password"]').inputValue(), '');
    await logout();
    await page.locator('#email').fill(email); await page.locator('#password').fill(password);
    await page.getByRole('button', {name: 'Ingresar', exact: false}).click();
    await page.getByRole('alert').filter({hasText: 'incorrectos'}).waitFor();
    await login(email, replacement, '/dashboard/nuevo-trabajador');
    results.push('Reset: clave anterior rechazada y nueva clave aceptada.');
    await logout();
    await login(adminEmail, adminPassword, '/dashboard/superadmin');
    await page.getByRole('link', {name: 'Nuevos trabajadores', exact: true}).click();
    await page.locator('[formcontrolname="search"]').fill(email);
    await page.getByRole('button', {name: 'Buscar', exact: true}).click();
    await page.getByRole('cell', {name: email, exact: true}).waitFor();
    results.push('Filtro de sidebar y búsqueda verificados.');
    await page.setViewportSize({width: 390, height: 844});
    await page.getByRole('button', {name: '☰ Menú', exact: true}).click();
    await page.locator('.sidebar.open').waitFor();
    await page.getByRole('link', {name: 'Inicio', exact: true}).click();
    await page.waitForURL(base + '/dashboard/superadmin');
    assert.equal(await page.locator('.sidebar.open').count(), 0);
    await page.getByText('Usuarios registrados recientemente', {exact: true}).waitFor();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    assert.equal(overflow, false);
    await page.screenshot({path: process.env.SA01_SCREENSHOT_MOBILE, fullPage: true});
    results.push('Menú móvil: abre, navega y se cierra; sin desbordamiento horizontal.');
    await page.setViewportSize({width: 1440, height: 1000});
    await page.screenshot({path: process.env.SA01_SCREENSHOT_DESKTOP, fullPage: true});
    await logout();
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({passed: true, user_id: userId, results}));
  } finally { await browser.close(); }
})().catch(error => {
  let message = error.name + ': ' + error.message;
  for (const name of ['SASPEL_DEV_SUPERADMIN_PASSWORD', 'SA01_TEST_PASSWORD']) {
    if (process.env[name]) message = message.split(process.env[name]).join('[REDACTED]');
  }
  console.error(message); process.exitCode = 1;
});
