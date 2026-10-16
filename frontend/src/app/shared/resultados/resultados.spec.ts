import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { of } from 'rxjs';
import { routes } from '../../app.routes';
import { API_URL } from '../../core/auth/api-url';
import { AuthUser } from '../../core/auth/auth.models';
import { AuthService } from '../../core/auth/auth.service';
import { Dashboard } from '../../features/dashboards/dashboard';
import { PsicologoDashboard } from '../../features/psicologo/dashboard';
import { PsicologoResultados } from '../../features/psicologo/resultados';
import { PsicologoTrabajadores } from '../../features/psicologo/trabajadores';
import { TrabajadorResultados } from '../../features/trabajador/resultados';
import { ResultadoResumen } from './resultados.models';

const worker: AuthUser = {
  id: 'a122e48a-64db-4dad-ae9d-11227dd72c19',
  email: 'ana@saspel.com',
  first_name: 'Ana',
  last_name: 'Pérez',
  role: 'TRABAJADOR',
  dashboard_path: '/dashboard/trabajador',
};
const psychologist: AuthUser = {
  ...worker,
  id: 'b122e48a-64db-4dad-ae9d-11227dd72c19',
  email: 'luis@saspel.com',
  first_name: 'Luis',
  role: 'PSICOLOGO',
  dashboard_path: '/dashboard/psicologo',
};
const result: ResultadoResumen = {
  id: 'c122e48a-64db-4dad-ae9d-11227dd72c19',
  instrumento: 'Evaluación registrada',
  version: '1.0',
  fecha: '2026-10-12T12:00:00Z',
  puntaje: '19.0000',
  rango: 'Moderado',
  interpretacion: 'Interpretación almacenada por el instrumento.',
  estado: 'FINALIZADA',
};
const workers = {
  cantidad: 1,
  trabajadores: [
    {
      id: worker.id,
      nombre_completo: 'Ana Pérez',
      email: worker.email,
      area: 'Operaciones',
      cargo: 'Analista',
      fecha_asignacion: '2026-10-12T12:00:00Z',
      estado: 'ACTIVA',
    },
  ],
};
const OWN_API = '/api/trabajador/resultados/';
const WORKERS_API = '/api/psicologo/trabajadores/';
const PRO_RESULT_API = '/api/psicologo/resultados/';
const ownPath = '/dashboard/trabajador/resultados';
const workersPath = '/dashboard/psicologo/trabajadores';
const proResultsPath = `${workersPath}/${worker.id}/resultados`;

describe('Resultados e historial T29', () => {
  let http: HttpTestingController;
  let identity: ReturnType<typeof signal<AuthUser>>;
  beforeEach(() => {
    identity = signal(worker);
    TestBed.configureTestingModule({
      providers: [
        provideRouter(routes),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: '/api' },
        {
          provide: AuthService,
          useValue: { user: identity, restoreSession: () => of(identity()), logout: vi.fn() },
        },
      ],
    });
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => {
    http.verify();
  });

  it('el dashboard del trabajador conserva identidad y ofrece Mis resultados', async () => {
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl(worker.dashboard_path, Dashboard);
    const link = [...harness.routeNativeElement!.querySelectorAll('a')].find((a) =>
      a.textContent?.includes('Mis resultados'),
    )!;
    expect(link.getAttribute('href')).toBe(ownPath);
    link.click();
    await harness.fixture.whenStable();
    http.expectOne(OWN_API).flush([result]);
    await harness.fixture.whenStable();
    expect(harness.routeNativeElement?.textContent).toContain('Mis resultados');
    expect(harness.routeNativeElement?.textContent).toContain('19');
  });

  it('listado propio y detalle muestran datos reales sin auditoría ni valores internos', async () => {
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl(ownPath, TrabajadorResultados);
    expect(harness.routeNativeElement?.textContent).toContain('Cargando resultados');
    const older = {
      ...result,
      id: 'd122e48a-64db-4dad-ae9d-11227dd72c19',
      instrumento: 'Versión previa',
      version: '0.9',
    };
    http.expectOne(OWN_API).flush([result, older]);
    await harness.fixture.whenStable();
    const titles = [...harness.routeNativeElement!.querySelectorAll('h2')].map(
      (h) => h.textContent,
    );
    expect(titles).toEqual(['Evaluación registrada', 'Versión previa']);
    const detailLink = harness.routeNativeElement!.querySelector('article a') as HTMLAnchorElement;
    detailLink.click();
    await harness.fixture.whenStable();
    http.expectOne(`${OWN_API}${result.id}/`).flush(result);
    await harness.fixture.whenStable();
    const text = harness.routeNativeElement!.textContent!;
    for (const value of [
      'Detalle del resultado',
      'Evaluación registrada',
      'Versión 1.0',
      '12/10/2026',
      '19',
      'Moderado',
      result.interpretacion,
      'FINALIZADA',
      'no constituye por sí solo un diagnóstico clínico',
    ]) {
      expect(text).toContain(value);
    }
    for (const value of [result.id, 'invertida', 'User_Create', 'password'])
      expect(text).not.toContain(value);
  });

  it('trabajador sin resultados muestra vacío y sin clasificación no inventa un rango', async () => {
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl(ownPath, TrabajadorResultados);
    http.expectOne(OWN_API).flush([]);
    await harness.fixture.whenStable();
    expect(harness.routeNativeElement?.textContent).toContain(
      'Aún no tienes resultados disponibles.',
    );
    await harness.navigateByUrl(`${ownPath}/${result.id}`, TrabajadorResultados);
    http.expectOne(`${OWN_API}${result.id}/`).flush({ ...result, rango: null, interpretacion: '' });
    await harness.fixture.whenStable();
    expect(harness.routeNativeElement?.textContent).toContain('Sin clasificación configurada');
    expect(harness.routeNativeElement?.textContent).not.toContain('Moderado');
  });

  it('error de consulta no se presenta como vacío, permite reintentar y no muestra datos internos', async () => {
    const harness = await RouterTestingHarness.create();
    const component = await harness.navigateByUrl(ownPath, TrabajadorResultados);
    http
      .expectOne(OWN_API)
      .flush({ detail: 'Traceback: internal SQL' }, { status: 500, statusText: 'Error' });
    await harness.fixture.whenStable();
    expect(harness.routeNativeElement?.textContent).toContain('No pudimos cargar los resultados');
    expect(harness.routeNativeElement?.textContent).not.toContain('Aún no tienes');
    expect(harness.routeNativeElement?.textContent).not.toContain('Traceback');
    component.vm.load();
    component.vm.load();
    http.expectOne(OWN_API).flush([result]);
    await harness.fixture.whenStable();
    expect(harness.routeNativeElement?.querySelector('[role=alert]')).toBeNull();
    expect(harness.routeNativeElement?.textContent).toContain(result.instrumento);
  });

  it('dashboard profesional muestra identidad real, cantidad y acceso a trabajadores', async () => {
    identity.set(psychologist);
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl(psychologist.dashboard_path, PsicologoDashboard);
    expect(harness.routeNativeElement?.textContent).toContain('Consultando asignaciones');
    http.expectOne(WORKERS_API).flush(workers);
    await harness.fixture.whenStable();
    const text = harness.routeNativeElement?.textContent;
    expect(text).toContain('Luis Pérez');
    expect(text).toContain('luis@saspel.com');
    expect(text).toContain('1 asignaciones profesionales activas');
    const link = harness.routeNativeElement?.querySelector('a');
    expect(link?.getAttribute('href')).toBe(workersPath);
  });

  it('mis trabajadores permite consultar resultados y abrir detalle consolidado', async () => {
    identity.set(psychologist);
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl(workersPath, PsicologoTrabajadores);
    http.expectOne(WORKERS_API).flush(workers);
    await harness.fixture.whenStable();
    for (const value of [
      'Ana Pérez',
      'ana@saspel.com',
      'Operaciones',
      'Analista',
      '12/10/2026',
      'ACTIVA',
    ]) {
      expect(harness.routeNativeElement?.textContent).toContain(value);
    }
    (harness.routeNativeElement!.querySelector('article a') as HTMLAnchorElement).click();
    await harness.fixture.whenStable();
    http.expectOne(`${WORKERS_API}${worker.id}/resultados/`).flush([result]);
    await harness.fixture.whenStable();
    expect(TestBed.inject(Router).url).toBe(proResultsPath);
    expect(harness.routeNativeElement?.textContent).toContain('Resultados del trabajador');
    (harness.routeNativeElement!.querySelector('article a') as HTMLAnchorElement).click();
    await harness.fixture.whenStable();
    http.expectOne(`${PRO_RESULT_API}${result.id}/`).flush(result);
    await harness.fixture.whenStable();
    expect(harness.routeNativeElement?.textContent).toContain(result.interpretacion);
    expect(harness.routeNativeElement?.querySelector('input, textarea')).toBeNull();
  });

  it('psicólogo sin asignaciones y trabajador sin resultados tienen mensajes propios', async () => {
    identity.set(psychologist);
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl(psychologist.dashboard_path, PsicologoDashboard);
    http.expectOne(WORKERS_API).flush({ cantidad: 0, trabajadores: [] });
    await harness.fixture.whenStable();
    expect(harness.routeNativeElement?.textContent).toContain(
      'No tienes trabajadores asignados actualmente.',
    );
    await harness.navigateByUrl(workersPath, PsicologoTrabajadores);
    http.expectOne(WORKERS_API).flush({ cantidad: 0, trabajadores: [] });
    await harness.fixture.whenStable();
    expect(harness.routeNativeElement?.textContent).toContain(
      'No tienes trabajadores asignados actualmente.',
    );
    await harness.navigateByUrl(proResultsPath, PsicologoResultados);
    http.expectOne(`${WORKERS_API}${worker.id}/resultados/`).flush([]);
    await harness.fixture.whenStable();
    expect(harness.routeNativeElement?.textContent).toContain(
      'Este trabajador aún no tiene resultados disponibles.',
    );
  });

  it('cambio de UUID elimina datos anteriores y maneja trabajador ajeno denegado', async () => {
    identity.set(psychologist);
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl(proResultsPath, PsicologoResultados);
    http.expectOne(`${WORKERS_API}${worker.id}/resultados/`).flush([result]);
    await harness.fixture.whenStable();
    const stranger = 'e122e48a-64db-4dad-ae9d-11227dd72c19';
    await harness.navigateByUrl(`${workersPath}/${stranger}/resultados`, PsicologoResultados);
    expect(harness.routeNativeElement?.textContent).not.toContain(result.instrumento);
    http
      .expectOne(`${WORKERS_API}${stranger}/resultados/`)
      .flush({}, { status: 404, statusText: 'Not found' });
    await harness.fixture.whenStable();
    expect(harness.routeNativeElement?.textContent).toContain(
      'No tienes acceso a estos resultados',
    );
    expect(harness.routeNativeElement?.querySelector('article')).toBeNull();
  });

  it('detalle propio ajeno denegado no deja un resultado previo visible', async () => {
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl(`${ownPath}/${result.id}`, TrabajadorResultados);
    http.expectOne(`${OWN_API}${result.id}/`).flush(result);
    const foreignId = 'f122e48a-64db-4dad-ae9d-11227dd72c19';
    await harness.navigateByUrl(`${ownPath}/${foreignId}`, TrabajadorResultados);
    http.expectOne(`${OWN_API}${foreignId}/`).flush({}, { status: 404, statusText: 'Not found' });
    await harness.fixture.whenStable();
    expect(harness.routeNativeElement?.textContent).toContain('No tienes acceso');
    expect(harness.routeNativeElement?.textContent).not.toContain(result.instrumento);
  });

  it('error de asignaciones permite reintentar sin confundirlo con cero trabajadores', async () => {
    identity.set(psychologist);
    const harness = await RouterTestingHarness.create();
    const component = await harness.navigateByUrl(workersPath, PsicologoTrabajadores);
    http.expectOne(WORKERS_API).flush({}, { status: 503, statusText: 'Unavailable' });
    await harness.fixture.whenStable();
    expect(harness.routeNativeElement?.textContent).toContain(
      'No pudimos consultar tus trabajadores',
    );
    expect(harness.routeNativeElement?.textContent).not.toContain('No tienes trabajadores');
    component.vm.load();
    http.expectOne(WORKERS_API).flush(workers);
    await harness.fixture.whenStable();
    expect(harness.routeNativeElement?.textContent).toContain('Ana Pérez');
  });

  it('TRABAJADOR no entra en ninguna ruta PSICOLOGO', async () => {
    const harness = await RouterTestingHarness.create();
    for (const path of [
      psychologist.dashboard_path,
      workersPath,
      proResultsPath,
      `/dashboard/psicologo/resultados/${result.id}`,
    ]) {
      await harness.navigateByUrl(path);
      expect(TestBed.inject(Router).url).toBe(worker.dashboard_path);
    }
    http.expectNone((request) => request.url.startsWith('/api/psicologo/'));
  });

  it('PSICOLOGO no entra en las rutas exclusivas de TRABAJADOR', async () => {
    identity.set(psychologist);
    const harness = await RouterTestingHarness.create();
    for (const path of [worker.dashboard_path, ownPath, `${ownPath}/${result.id}`]) {
      await harness.navigateByUrl(path);
      for (const request of http.match(WORKERS_API)) request.flush(workers);
      expect(TestBed.inject(Router).url).toBe(psychologist.dashboard_path);
    }
    http.expectNone((request) => request.url.startsWith(OWN_API));
  });
});
