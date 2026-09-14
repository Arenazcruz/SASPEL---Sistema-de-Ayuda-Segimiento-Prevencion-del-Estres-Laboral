/**
 * Comprueba acceso, redirecciones por rol y restauración con AuthService y HTTP simulado.
 * Si cambia el mapa de dashboards revisar estos escenarios junto a las rutas.
 */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  provideRouter,
  Router,
  RouterStateSnapshot,
  UrlTree,
} from '@angular/router';
import { Observable } from 'rxjs';
import { API_URL } from './api-url';
import { authGuard, guestGuard } from './auth.guard';
import { roleGuard } from './role.guard';
import { AuthService } from './auth.service';
import { FunctionalRole, ROLE_DASHBOARDS } from './auth.models';
import { TokenStorageService } from './token-storage.service';

describe('Guards de sesión y rol', () => {
  let requests: HttpTestingController;
  const route = {} as ActivatedRouteSnapshot;
  const state = {} as RouterStateSnapshot;
  beforeEach(() => {
    sessionStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: '/api' },
      ],
    });
    requests = TestBed.inject(HttpTestingController);
  });
  afterEach(() => {
    requests.verify();
    sessionStorage.clear();
  });

  it('sin sesión un dashboard redirige a login', () => {
    const result = TestBed.runInInjectionContext(() =>
      authGuard(route, state),
    ) as Observable<UrlTree>;
    result.subscribe((url) => expect(TestBed.inject(Router).serializeUrl(url)).toBe('/login'));
  });

  // La sesión no se acepta hasta recibir identidad de me; un token local no basta.
  it('auth guard consulta me antes de permitir la entrada', () => {
    TestBed.inject(TokenStorageService).save({ access: 'access', refresh: 'refresh' });
    (TestBed.runInInjectionContext(() => authGuard(route, state)) as Observable<boolean>).subscribe(
      (result) => expect(result).toBe(true),
    );
    requests
      .expectOne('/api/auth/me/')
      .flush({
        id: 1,
        email: 'test@example.com',
        first_name: '',
        last_name: '',
        role: 'ADMIN',
        dashboard_path: '/dashboard/admin',
      });
  });

  it('login redirige a una persona con sesión restaurada', () => {
    TestBed.inject(TokenStorageService).save({ access: 'access', refresh: 'refresh' });
    (
      TestBed.runInInjectionContext(() => guestGuard(route, state)) as Observable<UrlTree>
    ).subscribe((url) =>
      expect(TestBed.inject(Router).serializeUrl(url)).toBe('/dashboard/psicologo'),
    );
    requests
      .expectOne('/api/auth/me/')
      .flush({
        id: 1,
        email: 'test@example.com',
        first_name: '',
        last_name: '',
        role: 'PSICOLOGO',
        dashboard_path: '/dashboard/psicologo',
      });
  });

  for (const role of Object.keys(ROLE_DASHBOARDS) as FunctionalRole[]) {
    it(`permite el panel de ${role} y redirige cualquier otro`, () => {
      TestBed.inject(TokenStorageService).save({ access: 'access', refresh: 'refresh' });
      TestBed.inject(AuthService).restoreSession().subscribe();
      requests
        .expectOne('/api/auth/me/')
        .flush({
          id: 1,
          email: 'test@example.com',
          first_name: '',
          last_name: '',
          role,
          dashboard_path: ROLE_DASHBOARDS[role],
        });
      const allowedRoute = new ActivatedRouteSnapshot();
      allowedRoute.data = { role };
      const allowed = TestBed.runInInjectionContext(() => roleGuard(allowedRoute, state));
      expect(allowed).toBe(true);
      const deniedRoute = new ActivatedRouteSnapshot();
      deniedRoute.data = { role: 'OTRO' };
      const denied = TestBed.runInInjectionContext(() => roleGuard(deniedRoute, state));
      expect(TestBed.inject(Router).serializeUrl(denied as UrlTree)).toBe(ROLE_DASHBOARDS[role]);
    });
  }
});
