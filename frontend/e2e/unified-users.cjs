// Ejecutado por backend/tests/test_superadmin_browser.py sobre la BD temporal.
const { chromium } = require(process.env.SASPEL_PLAYWRIGHT_MODULE);
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(12000);
  const base = process.env.SASPEL_FRONTEND_URL || 'http://localhost:4200';
  const password = process.env.SASPEL_TEST_PASSWORD;
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('dialog', (dialog) => dialog.accept());
  await page.route('**/api/**', async (route) => {
    const url = new URL(route.request().url());
    const response = await route.fetch({
      url: process.env.SASPEL_TEST_API + url.pathname + url.search,
    });
    await route.fulfill({ response });
  });
  const dialog = page.getByRole('dialog');
  const row = () =>
    page
      .getByRole('row')
      .filter({ has: page.getByRole('cell', { name: 'jesus.cruz@saspel.com', exact: true }) });
  async function login(email, target) {
    await page.goto(base + '/login');
    await page.locator('#email').fill(email);
    await page.locator('#password').fill(password);
    await page.getByRole('button', { name: /Ingresar/ }).click();
    await page.waitForURL(base + target);
  }
  async function logout() {
    await page.getByRole('button', { name: 'Cerrar sesión' }).click();
    await page.waitForURL(base + '/login');
  }
  try {
    await login(process.env.SASPEL_TEST_EMAIL, '/dashboard/superadmin');
    await page.getByRole('link', { name: 'Usuarios', exact: true }).click();
    await page.getByRole('heading', { name: 'Usuarios', exact: true }).waitFor();
    assert.equal(await page.locator('#people-menu a, #people-menu button').count(), 2);
    const categories = page.getByRole('navigation', { name: 'Categorías de usuarios' });
    assert.equal(await categories.getByRole('button').count(), 5);
    // Cada categoría mantiene el mismo componente y solicita filtros al mismo endpoint.
    for (const [label, role] of [
      ['Psicólogos', 'PSICOLOGO'],
      ['Administradores', 'ADMINISTRADORES'],
      ['Nuevos trabajadores', 'NUEVO_TRABAJADOR'],
    ]) {
      const response = page.waitForResponse(
        (r) =>
          r.url().includes('/superadmin/users/?') &&
          new URL(r.url()).searchParams.get('role') === role,
      );
      await categories.getByRole('button', { name: label, exact: true }).click();
      assert.equal((await response).status(), 200);
      assert.equal(await page.locator('app-user-list').count(), 1);
    }
    await page.getByRole('link', { name: 'Nuevo usuario', exact: true }).click();
    await dialog.waitFor();
    assert.equal(await dialog.locator('[formcontrolname="email"]').count(), 0);
    await dialog.locator('[formcontrolname="first_name"]').fill('Jesús Gabriel');
    await dialog.locator('[formcontrolname="last_name"]').fill('Crúz');
    await dialog.locator('[formcontrolname="apellido_materno"]').fill('Lavadenz');
    await dialog.locator('[formcontrolname="codigo_empleado"]').fill('BROWSER-001');
    await dialog.locator('[formcontrolname="password"]').fill(password);
    await dialog.locator('[formcontrolname="password_confirmation"]').fill(password);
    assert.equal(await dialog.locator('input[type="email"]').inputValue(), 'jesus.cruz@saspel.com');
    assert.equal(await dialog.locator('input[type="email"]').getAttribute('readonly'), '');
    const creation = page.waitForResponse(
      (r) => r.request().method() === 'POST' && r.url().endsWith('/superadmin/users/'),
    );
    await dialog.getByRole('button', { name: 'Crear usuario', exact: true }).click();
    const created = await (await creation).json();
    assert.equal(created.email, 'jesus.cruz@saspel.com');
    await dialog.waitFor({ state: 'hidden' });
    assert.equal(new URL(page.url()).searchParams.get('role'), 'NUEVO_TRABAJADOR');
    await row().waitFor();
    await row().getByRole('link', { name: 'Editar', exact: true }).click();
    await dialog.waitFor();
    await dialog.locator('[formcontrolname="telefono"]').fill('+591 70000000');
    await dialog.locator('[formcontrolname="first_name"]').fill('Jesús Editado');
    assert.equal(await dialog.locator('input[type="email"]').inputValue(), created.email);
    await dialog.getByRole('button', { name: 'Guardar cambios', exact: true }).click();
    await dialog.waitFor({ state: 'hidden' });
    await row()
      .getByRole('cell', { name: /Jesús Editado/ })
      .waitFor();
    await row().getByRole('link', { name: 'Ver', exact: true }).click();
    await dialog.getByText('+591 70000000', { exact: true }).waitFor();
    await dialog.getByRole('link', { name: 'Editar usuario', exact: true }).click();
    await dialog.getByRole('heading', { name: 'Editar usuario', exact: true }).waitFor();
    await page.keyboard.press('Escape');
    await dialog.waitFor({ state: 'hidden' });
    await row().getByRole('button', { name: 'Desactivar', exact: true }).click();
    await row().getByRole('button', { name: 'Reactivar', exact: true }).waitFor();
    await logout();
    await page.locator('#email').fill(created.email);
    await page.locator('#password').fill(password);
    await page.getByRole('button', { name: /Ingresar/ }).click();
    await page.getByRole('alert').filter({ hasText: 'no está habilitada' }).waitFor();
    await login(process.env.SASPEL_TEST_EMAIL, '/dashboard/superadmin');
    await page.getByRole('link', { name: 'Usuarios', exact: true }).click();
    await row().getByRole('button', { name: 'Reactivar', exact: true }).click();
    await row().getByRole('button', { name: 'Desactivar', exact: true }).waitFor();
    await logout();
    await login(created.email, '/dashboard/nuevo-trabajador');
    await logout();
    await login(process.env.SASPEL_TEST_EMAIL, '/dashboard/superadmin');
    await page.goto(base + '/dashboard/superadmin/personas/psicologos?search=Ana');
    await page.waitForURL(
      (url) => url.pathname.endsWith('/personas') && url.searchParams.get('role') === 'PSICOLOGO',
    );
    assert.equal(new URL(page.url()).searchParams.get('search'), 'Ana');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('link', { name: 'Nuevo usuario', exact: true }).click();
    await dialog.waitFor();
    assert.equal(await dialog.evaluate((el) => el.scrollWidth > el.clientWidth), false);
    await page.keyboard.press('Escape');
    await dialog.waitFor({ state: 'hidden' });
    assert.deepEqual(errors, []);
    console.log(
      'OK: filtros, modal crear/editar/ver, correo, estado, login, rutas anteriores y móvil.',
    );
  } finally {
    await page.unrouteAll({ behavior: 'ignoreErrors' });
    await browser.close();
  }
})().catch((error) => {
  console.error(String(error).replaceAll(process.env.SASPEL_TEST_PASSWORD, '[REDACTED]'));
  process.exitCode = 1;
});
