import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { of } from 'rxjs';
import { routes } from '../../app.routes';
import { API_URL } from '../../core/auth/api-url';
import { authGuard } from '../../core/auth/auth.guard';
import { AuthUser, ROLE_DASHBOARDS } from '../../core/auth/auth.models';
import { AuthService } from '../../core/auth/auth.service';
import { primerAccesoGuard } from '../../core/auth/primer-acceso.guard';
import { roleGuard } from '../../core/auth/role.guard';
import { TokenStorageService } from '../../core/auth/token-storage.service';
import { Dashboard } from '../dashboards/dashboard';
import { SuperadminLayout } from '../superadmin/layout/superadmin-layout';
import { NuevoTrabajadorDashboard } from './dashboard';
import { DashboardResumen, EvaluacionInicial } from './dashboard.models';

const URL = '/api/nuevo-trabajador/dashboard/';
const user: AuthUser = {
  id: 'e6b90f86-a65f-447a-8984-dd956d326001',
  email: 'ana.prueba@saspel.com',
  first_name: 'Ana María',
  last_name: 'Prueba',
  role: 'NUEVO_TRABAJADOR',
  dashboard_path: '/dashboard/nuevo-trabajador',
  primer_acceso: {
    debe_cambiar_password: false,
    politicas_pendientes: [],
    completo: true,
    siguiente_ruta: '/dashboard/nuevo-trabajador',
  },
};
function resumen(estado: EvaluacionInicial['estado']): DashboardResumen {
  return {
    evaluacion_inicial: {
      estado,
      puede_iniciar: false,
      asignacion_id: estado === 'SIN_ASIGNAR' ? null : 'e6b90f86-a65f-447a-8984-dd956d326002',
      instrumento_id: estado === 'SIN_ASIGNAR' ? null : 'e6b90f86-a65f-447a-8984-dd956d326003',
      nombre: estado === 'SIN_ASIGNAR' ? null : 'Evaluación institucional de prueba',
      version: estado === 'SIN_ASIGNAR' ? null : '2.1',
      fecha_asignacion: estado === 'SIN_ASIGNAR' ? null : '2026-10-01T12:00:00Z',
      fecha_limite: null,
    },
  };
}

describe('Dashboard propio del nuevo trabajador', () => {
  let http: HttpTestingController;
  let auth: {
    user: ReturnType<typeof signal<AuthUser | null>>;
    logout: ReturnType<typeof vi.fn>;
    restoreSession: ReturnType<typeof vi.fn>;
  };
  beforeEach(() => {
    auth = {
      user: signal<AuthUser | null>(user),
      logout: vi.fn(),
      restoreSession: vi.fn().mockReturnValue(of(user)),
    };
    TestBed.configureTestingModule({
      providers: [
        provideRouter(routes),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: '/api' },
        { provide: AuthService, useValue: auth },
      ],
    });
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());

  it('muestra identidad real, bienvenida, proceso y privacidad sin pedir aceptación', async () => {
    const fixture = TestBed.createComponent(NuevoTrabajadorDashboard);
    http.expectOne(URL).flush(resumen('SIN_ASIGNAR'));
    await fixture.whenStable();
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Ana María Prueba');
    expect(text).toContain(user.email);
    expect(text).toContain('Bienvenido/a, Ana');
    expect(text).toContain('monitoreo, seguimiento y prevención del estrés laboral');
    expect(text).toContain('conservar sus resultados');
    expect(text).toContain('no sustituye un diagnóstico clínico');
    expect(text).toContain('información psicológica no es pública');
    expect(text).toContain('políticas que aceptaste');
    expect(fixture.nativeElement.querySelectorAll('ol li')).toHaveLength(4);
    expect(fixture.nativeElement.querySelector('input[type=checkbox]')).toBeNull();
  });

  for (const [estado, mensaje] of [
    ['SIN_ASIGNAR', 'Tu evaluación inicial todavía no fue habilitada.'],
    ['PENDIENTE', 'Evaluación disponible'],
    ['EN_PROGRESO', 'Evaluación en progreso'],
    ['COMPLETADA', 'Evaluación inicial completada'],
  ] as const) {
    it(`representa el estado real ${estado}`, async () => {
      const fixture = TestBed.createComponent(NuevoTrabajadorDashboard);
      await fixture.whenStable();
      expect(fixture.nativeElement.textContent).toContain('Consultando tu evaluación');
      expect(fixture.nativeElement.textContent).not.toContain('todavía no fue habilitada');
      const request = http.expectOne(URL);
      expect(request.request.method).toBe('GET');
      expect(request.request.params.keys()).toEqual([]);
      request.flush(resumen(estado));
      await fixture.whenStable();
      expect(fixture.nativeElement.textContent).toContain(mensaje);
      const button = fixture.nativeElement.querySelector('.evaluation button');
      if (estado === 'PENDIENTE') {
        expect(button.textContent).toContain('Comenzar evaluación');
        expect(button.disabled).toBe(true);
        expect(fixture.nativeElement.textContent).toContain(
          'La evaluación inicial todavía está siendo configurada.',
        );
      } else if (estado === 'EN_PROGRESO') {
        expect(button.textContent).toContain('Continuar evaluación');
        expect(button.disabled).toBe(false);
      } else {
        expect(button).toBeNull();
      }
      if (estado !== 'SIN_ASIGNAR') {
        expect(fixture.nativeElement.textContent).toContain('Evaluación institucional de prueba');
        expect(fixture.nativeElement.textContent).toContain('2.1');
      }
      expect(fixture.nativeElement.querySelector('.evaluation a')).toBeNull();
      expect(fixture.nativeElement.textContent).not.toContain('Puntaje');
    });
  }

  it('muestra fecha límite cuando existe', async () => {
    const fixture = TestBed.createComponent(NuevoTrabajadorDashboard);
    const data = resumen('PENDIENTE');
    data.evaluacion_inicial.fecha_limite = '2026-10-15T12:00:00Z';
    http.expectOne(URL).flush(data);
    await fixture.whenStable();
    expect(fixture.nativeElement.textContent).toContain('15/10/2026');
  });

  it('un error no se presenta como SIN_ASIGNAR y permite reintentar', async () => {
    const fixture = TestBed.createComponent(NuevoTrabajadorDashboard);
    http.expectOne(URL).flush({}, { status: 500, statusText: 'Error' });
    await fixture.whenStable();
    expect(fixture.nativeElement.querySelector('[role=alert]').textContent).toContain(
      'No pudimos consultar',
    );
    expect(fixture.nativeElement.textContent).not.toContain('todavía no fue habilitada');
    fixture.nativeElement.querySelector('.evaluation button').click();
    http.expectOne(URL).flush(resumen('COMPLETADA'));
    await fixture.whenStable();
    expect(fixture.nativeElement.textContent).toContain('Evaluación inicial completada');
  });

  it('cerrar sesión llama al servicio de autenticación', async () => {
    const fixture = TestBed.createComponent(NuevoTrabajadorDashboard);
    http.expectOne(URL).flush(resumen('SIN_ASIGNAR'));
    await fixture.whenStable();
    fixture.nativeElement.querySelector('header button').click();
    expect(auth.logout).toHaveBeenCalledOnce();
  });

  it('la ruta protegida carga el feature propio', async () => {
    const harness = await RouterTestingHarness.create();
    const component = await harness.navigateByUrl(user.dashboard_path, NuevoTrabajadorDashboard);
    http.expectOne(URL).flush(resumen('SIN_ASIGNAR'));
    expect(component).toBeInstanceOf(NuevoTrabajadorDashboard);
    expect(auth.restoreSession).toHaveBeenCalled();
  });

  it('mantiene AuthGuard, primerAccesoGuard y RoleGuard', () => {
    const parent = routes.find((route) => route.path === 'dashboard')!;
    expect(parent.canActivate).toContain(authGuard);
    expect(parent.canActivateChild).toContain(primerAccesoGuard);
    const child = parent.children!.find((route) => route.path === 'nuevo-trabajador')!;
    expect(child.canActivate).toContain(roleGuard);
    expect(child.data?.['role']).toBe('NUEVO_TRABAJADOR');
  });

  for (const role of ['TRABAJADOR', 'ADMIN'] as const) {
    it(`conserva el dashboard genérico de ${role} e impide acceder al nuevo`, async () => {
      const identity: AuthUser = {
        ...user,
        role,
        dashboard_path: ROLE_DASHBOARDS[role],
        primer_acceso: undefined,
      };
      auth.user.set(identity);
      auth.restoreSession.mockReturnValue(of(identity));
      const harness = await RouterTestingHarness.create();
      await harness.navigateByUrl(user.dashboard_path, Dashboard);
      expect(TestBed.inject(Router).url).toBe(identity.dashboard_path);
      http.expectNone(URL);
    });
  }

  it('conserva el componente y las rutas propias de Superadmin', async () => {
    const child = routes
      .find((route) => route.path === 'dashboard')!
      .children!.find((route) => route.path === 'superadmin')!;
    const loader = child.loadComponent as () => Promise<unknown>;
    expect(await loader()).toBe(SuperadminLayout);
    expect(child.loadChildren).toBeDefined();
    expect(child.canActivate).toContain(roleGuard);
  });

  for (const paso of ['password', 'politicas']) {
    it(`primer acceso pendiente redirige a ${paso} sin consultar el dashboard`, async () => {
      const pendiente: AuthUser = {
        ...user,
        primer_acceso: {
          debe_cambiar_password: paso === 'password',
          politicas_pendientes: ['policy'],
          completo: false,
          siguiente_ruta: `/primer-acceso/${paso}`,
        },
      };
      auth.user.set(pendiente);
      auth.restoreSession.mockReturnValue(of(pendiente));
      const harness = await RouterTestingHarness.create();
      await harness.navigateByUrl(user.dashboard_path);
      expect(TestBed.inject(Router).url).toBe(`/primer-acceso/${paso}`);
      if (paso === 'politicas') {
        http.expectOne('/api/auth/primer-acceso/politicas/').flush([]);
        http.expectOne('/api/auth/primer-acceso/').flush(pendiente.primer_acceso!);
      }
      http.expectNone(URL);
    });
  }

  it('sin sesión redirige al login sin consultar evaluaciones', async () => {
    auth.user.set(null);
    auth.restoreSession.mockReturnValue(of(null));
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl(user.dashboard_path);
    expect(TestBed.inject(Router).url).toBe('/login');
    http.expectNone(URL);
  });
});

describe('Logout del nuevo trabajador con AuthService real', () => {
  it('borra tokens e identidad y navega a login', async () => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: '/api' },
      ],
    });
    const http = TestBed.inject(HttpTestingController);
    const auth = TestBed.inject(AuthService);
    const storage = TestBed.inject(TokenStorageService);
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    auth.login(user.email, 'Temporal-582!').subscribe();
    http
      .expectOne('/api/auth/login/')
      .flush({ user, dashboard_path: user.dashboard_path, access: 'access', refresh: 'refresh' });
    const fixture = TestBed.createComponent(NuevoTrabajadorDashboard);
    http.expectOne(URL).flush(resumen('SIN_ASIGNAR'));
    await fixture.whenStable();
    fixture.nativeElement.querySelector('header button').click();
    expect(auth.user()).toBeNull();
    expect(storage.access).toBeFalsy();
    expect(storage.refresh).toBeFalsy();
    expect(navigate).toHaveBeenCalledWith('/login');
    http.verify();
    vi.restoreAllMocks();
  });
});
