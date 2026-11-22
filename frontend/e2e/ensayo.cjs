// Guion H4. LiveServer aporta una API y un dataset exclusivos por ejecución.
const { chromium } = require(process.env.SASPEL_PLAYWRIGHT_MODULE);
const assert = require('node:assert/strict');

(async () => {
  const base = process.env.SASPEL_FRONTEND_URL;
  const api = process.env.SASPEL_TEST_API;
  const password = process.env.SASPEL_DEMO_PASSWORD;
  const browser = await chromium.launch({channel:'msedge', headless:true});
  const jsErrors = [];
  async function login(alias, landing) {
    const ctx = await browser.newContext({timezoneId:'America/La_Paz'});
    const page = await ctx.newPage();
    page.setDefaultTimeout(12000);
    page.on('pageerror', e => jsErrors.push(e.message));
    await page.route('**/api/**', async route => {
      const url = new URL(route.request().url());
      await route.fulfill({response: await route.fetch({url: api + url.pathname + url.search})});
    });
    await page.goto(base+'/login');
    await page.locator('#email').fill('demo.'+alias+'@saspel.com');
    await page.locator('#password').fill(password);
    await page.getByRole('button',{name:/Ingresar/}).click();
    await page.waitForURL(base+landing);
    return page;
  }
  try {
    const sa = await login('sa','/dashboard/superadmin');
    await sa.goto(base+'/dashboard/administracion/politicas');
    await sa.getByText('Política de ensayo · demo-1').waitFor();
    const admin = await login('admin','/dashboard/admin');
    await admin.goto(base+'/dashboard/admin/personas');
    await admin.getByText('demo.trab@saspel.com',{exact:true}).first().waitFor();
    const nuevo = await login('nuevo','/primer-acceso/password');
    await nuevo.locator('#new-password').fill(password+'B7!');
    await nuevo.locator('#password-confirmation').fill(password+'B7!');
    await nuevo.locator('button[type=submit]').click();
    await nuevo.getByRole('checkbox').check();
    await nuevo.getByRole('button',{name:'Aceptar y continuar'}).click();
    await nuevo.getByRole('button',{name:'Comenzar evaluación'}).click();
    const items = nuevo.locator('app-evaluacion-pregunta');
    await items.first().waitFor();
    assert.equal(await items.count(),10);
    for (const item of await items.all()) await item.getByRole('radio').first().check();
    await nuevo.getByRole('button',{name:'Finalizar evaluación'}).click();
    await nuevo.getByRole('heading',{name:'Evaluación inicial completada'}).waitFor();
    await nuevo.getByRole('button',{name:'Continuar a mi panel'}).click();
    await nuevo.waitForURL(base+'/dashboard/trabajador');
    const w = await login('trab','/dashboard/trabajador');
    await w.getByRole('link',{name:'Mi evolución del estrés',exact:true}).first().click();
    await w.getByRole('table').waitFor();
    assert.equal(await w.locator('tbody tr').count(),2);
    await w.goto(base+'/dashboard/trabajador/recomendaciones');
    await w.getByText('Registrar una pausa durante la jornada de demostración.').waitFor();
    const psy = await login('psi','/dashboard/psicologo');
    await psy.goto(base+'/dashboard/psicologo/citas');
    await psy.getByRole('button',{name:'Aceptar',exact:true}).click();
    await psy.getByText(/CONFIRMADA/).waitFor();
    await psy.goto(base+'/dashboard/notificaciones');
    await psy.getByRole('link',{name:'Consultar resultado de origen'}).first().click();
    await psy.getByRole('heading',{name:'Detalle del resultado'}).waitFor();
    await w.goto(base+'/dashboard/notificaciones');
    await w.getByText(/Cita: Confirmada/i).waitFor();
    await admin.goto(base+'/dashboard/reportes');
    await admin.locator('[name=tipo]').selectOption('citas');
    await admin.getByRole('button',{name:'Consultar',exact:true}).click();
    await admin.getByRole('button',{name:'Exportar CSV'}).waitFor();
    const download = admin.waitForEvent('download');
    await admin.getByRole('button',{name:'Exportar CSV'}).click();
    assert.match((await download).suggestedFilename(),/\.csv$/i);
    await sa.goto(base+'/dashboard/administracion/auditoria');
    await sa.getByText(/eventos · Página/).waitFor();
    await sa.locator('article').first().waitFor();
    assert.deepEqual(jsErrors,[]);
  } finally {await browser.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
