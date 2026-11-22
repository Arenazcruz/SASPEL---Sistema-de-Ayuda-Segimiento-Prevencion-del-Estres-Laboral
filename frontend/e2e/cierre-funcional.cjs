// Datos generados por test_cierre_browser.py en PostgreSQL efímero.
const { chromium } = require(process.env.SASPEL_PLAYWRIGHT_MODULE);
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const base = process.env.SASPEL_FRONTEND_URL || 'http://127.0.0.1:4300';
  const fixture = JSON.parse(process.env.SASPEL_TEST_FIXTURE);
  const errors = [];
  const pages = [];
  async function session(email, role) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, timezoneId: 'America/La_Paz' });
    const page = await context.newPage();
    pages.push(page);
    page.setDefaultTimeout(12000);
    page.on('pageerror', e => errors.push(e.message));
    await page.route('**/api/**', async route => {
      const url = new URL(route.request().url());
      const response = await route.fetch({ url: process.env.SASPEL_TEST_API + url.pathname + url.search });
      await route.fulfill({ response });
    });
    await page.goto(base + '/login');
    await page.locator('#email').fill(email);
    await page.locator('#password').fill(process.env.SASPEL_TEST_PASSWORD);
    await page.getByRole('button', { name: /Ingresar/ }).click();
    await page.waitForURL(base + '/dashboard/' + role);
    return page;
  }
  async function screenshot(page, name) {
    if (process.env.SASPEL_SCREENSHOTS) {
      fs.mkdirSync(process.env.SASPEL_SCREENSHOTS, { recursive: true });
      await page.screenshot({ path: path.join(process.env.SASPEL_SCREENSHOTS, name + '.png'), fullPage: true });
    }
  }
  try {
    const psy = await session(fixture.psy_email, 'psicologo');
    const worker = await session(fixture.worker_email, 'trabajador');
    for (let i = 0; i < 2; i++) {
      await psy.goto(base + `/dashboard/psicologo/trabajadores/${fixture.worker}/instrumentos`);
      await psy.locator('select[name="instrumento"]').selectOption(fixture.instrument);
      await psy.getByRole('button', { name: 'Asignar', exact: true }).click();
      await psy.getByText('Instrumento asignado.', { exact: true }).waitFor();
      await worker.goto(base + '/dashboard/trabajador/instrumentos');
      await worker.getByRole('link', { name: 'Responder', exact: true }).click();
      await worker.getByRole('button', { name: 'Comenzar evaluación' }).click();
      await worker.getByRole('radio').first().check();
      await worker.getByRole('button', { name: 'Guardar progreso' }).click();
      await worker.reload();
      await worker.getByRole('radio').first().waitFor();
      assert.equal(await worker.getByRole('radio').first().isChecked(), true);
      await worker.getByRole('button', { name: 'Finalizar evaluación' }).click();
      await worker.getByRole('heading', { name: 'Evaluación completada', exact: true }).waitFor();
    }
    await worker.goto(base + '/dashboard/trabajador/evolucion');
    await worker.getByRole('table').waitFor();
    assert.equal(await worker.locator('tbody tr').count(), 2);
    await worker.getByRole('img', {name:/Puntajes en orden temporal/}).waitFor();
    assert.match(await worker.locator('svg polyline').getAttribute('points'), /^20,/);
    await screenshot(worker, 'evolucion-desktop');
    await worker.setViewportSize({ width: 390, height: 844 });
    await screenshot(worker, 'evolucion-mobile');
    assert.ok(await worker.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'Desbordamiento móvil');
    await psy.goto(base + `/dashboard/psicologo/seguimientos/${fixture.seguimiento}/recomendaciones`);
    await psy.getByLabel('Texto', { exact: true }).fill('Recomendación de demostración sin datos clínicos.');
    await psy.getByRole('button', { name: 'Guardar', exact: true }).click();
    await psy.getByRole('button', { name: 'Iniciar', exact: true }).click();
    await psy.getByText(/EN_PROGRESO/).waitFor();
    await psy.getByRole('button', { name: 'Completar', exact: true }).click();
    await psy.getByText(/COMPLETADA/).waitFor();
    await screenshot(psy, 'recomendaciones-desktop');
    await worker.goto(base + '/dashboard/perfil');
    await worker.getByLabel('Teléfono', { exact: true }).fill('59170000000');
    await worker.getByRole('button', { name: 'Guardar perfil' }).click();
    await worker.getByText('Perfil actualizado.', { exact: true }).waitFor();
    await worker.reload();
    assert.equal(await worker.getByLabel('Teléfono', { exact: true }).inputValue(), '59170000000');
    // El guard evita la interfaz clínica profesional al trabajador.
    await worker.goto(base + `/dashboard/psicologo/seguimientos/${fixture.seguimiento}/recomendaciones`);
    await worker.waitForURL(base + '/dashboard/trabajador');
    const admin = await session(fixture.admin_email, 'admin');
    await admin.goto(base + '/dashboard/admin/institucion/cargos');
    await admin.getByLabel('Nombre *', {exact:true}).fill('Cargo E2E sintético');
    await admin.getByRole('button', {name:'Guardar',exact:true}).click();
    await admin.getByText('Registro guardado.', {exact:true}).waitFor();
    await admin.goto(base + '/dashboard/admin/institucion/areas');
    await admin.getByLabel('Nombre *', {exact:true}).fill('Área E2E sintética');
    await admin.getByRole('button', {name:'Guardar',exact:true}).click();
    const row = admin.getByRole('row').filter({hasText:'Área E2E sintética'});
    await row.getByRole('link', {name:'Configurar cargos'}).click();
    await admin.getByLabel('Cargo E2E sintético', {exact:true}).check();
    await admin.getByRole('button', {name:'Guardar cargos del área'}).click();
    await admin.getByText('Cargos del área actualizados.', {exact:true}).waitFor();
    await admin.reload();
    assert.equal(await admin.getByLabel('Cargo E2E sintético', {exact:true}).isChecked(),true);
    await admin.goto(base + '/dashboard/admin/personas/nuevo');
    await admin.locator('.sa-form select[formcontrolname="role"]').waitFor();
    assert.deepEqual(await admin.locator('.sa-form select[formcontrolname="role"] option').evaluateAll(options=>options.map(x=>x.value)),['NUEVO_TRABAJADOR','PSICOLOGO']);
    await screenshot(admin,'administracion-institucional');
    assert.deepEqual(errors, []);
    console.log('E2E H4: asignación, guardado/recuperación, finalización, evolución, móvil, recomendaciones, perfil y guard: OK');
  } catch (error) {
    console.error('Fallo E2E:', error.message.replace(/Bearer [A-Za-z0-9._-]+/g, 'Bearer [REDACTED]'));
    for (let i=0;i<pages.length;i++) {
      console.error('Pantalla sintética', pages[i].url(), await pages[i].locator('body').innerText());
      await screenshot(pages[i], 'error-h4-'+i);
    }
    throw error;
  } finally {
    for (const page of pages) await page.unrouteAll({behavior:'ignoreErrors'});
    await browser.close();
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
