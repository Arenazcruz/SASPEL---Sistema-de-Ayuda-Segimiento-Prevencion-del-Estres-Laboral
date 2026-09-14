/**
 * Comprueba AuthService e interceptor con HTTP simulado: login, restauración, renovación
 * compartida, exclusión de URLs ajenas y respuestas tardías tras logout. Los nombres de cada
 * prueba describen el escenario; no usa cuentas reales.
 */
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { API_URL } from './api-url';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from './auth.service';
import { AuthUser } from './auth.models';
import { TokenStorageService } from './token-storage.service';

const user: AuthUser = {
  id: 1,
  email: 'test@example.com',
  first_name: 'Ana',
  last_name: '',
  role: 'TRABAJADOR',
  dashboard_path: '/dashboard/trabajador',
};
describe('AuthService e interceptor', () => {
  let auth: AuthService;
  let http: HttpClient;
  let requests: HttpTestingController;
  let storage: TokenStorageService;
  let navigate: ReturnType<typeof vi.spyOn>;
  beforeEach(() => {
    sessionStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: '/api' },
      ],
    });
    auth = TestBed.inject(AuthService);
    http = TestBed.inject(HttpClient);
    requests = TestBed.inject(HttpTestingController);
    storage = TestBed.inject(TokenStorageService);
    navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
  });
  afterEach(() => {
    requests.verify();
    sessionStorage.clear();
  });

  it('inicia sesión sin enviar un token anterior y no guarda la contraseña', () => {
    storage.save({ access: 'old', refresh: 'old-refresh' });
    auth
      .login('test@example.com', 'test-password')
      .subscribe((result) => expect(result.role).toBe('TRABAJADOR'));
    const request = requests.expectOne('/api/auth/login/');
    expect(request.request.headers.has('Authorization')).toBe(false);
    expect(request.request.body.email).toBe('test@example.com');
    request.flush({
      access: 'access',
      refresh: 'refresh',
      user,
      dashboard_path: user.dashboard_path,
    });
    expect(storage.access).toBe('access');
    expect(storage.refresh).toBe('refresh');
    expect(auth.user()?.email).toBe(user.email);
    expect(Object.values(sessionStorage).join()).not.toContain('test-password');
  });

  it('restaura el rol real consultando me', () => {
    storage.save({ access: 'access', refresh: 'refresh' });
    auth.restoreSession().subscribe((result) => expect(result).toEqual(user));
    const request = requests.expectOne('/api/auth/me/');
    expect(request.request.headers.get('Authorization')).toBe('Bearer access');
    request.flush(user);
    expect(auth.user()).toEqual(user);
  });

  it('sin tokens no intenta recuperar identidad', () => {
    auth.restoreSession().subscribe((result) => expect(result).toBeNull());
    requests.expectNone('/api/auth/me/');
  });

  it('logout elimina tokens e identidad y vuelve al login', () => {
    storage.save({ access: 'access', refresh: 'refresh' });
    auth.restoreSession().subscribe();
    requests.expectOne('/api/auth/me/').flush(user);
    auth.logout();
    expect(storage.access).toBeNull();
    expect(storage.refresh).toBeNull();
    expect(auth.user()).toBeNull();
    expect(navigate).toHaveBeenCalledWith('/login');
  });

  it('renueva una sola vez y reintenta me cuando vence access', () => {
    storage.save({ access: 'expired', refresh: 'refresh' });
    auth.restoreSession().subscribe((result) => expect(result).toEqual(user));
    requests.expectOne('/api/auth/me/').flush({}, { status: 401, statusText: 'Unauthorized' });
    const renewal = requests.expectOne('/api/auth/refresh/');
    expect(renewal.request.headers.has('Authorization')).toBe(false);
    renewal.flush({ access: 'new-access' });
    const retried = requests.expectOne('/api/auth/me/');
    expect(retried.request.headers.get('Authorization')).toBe('Bearer new-access');
    retried.flush(user);
    expect(storage.access).toBe('new-access');
  });

  // Dos requests reciben 401 antes de renovar: deben compartir un solo POST de refresh.
  it('comparte la renovación entre peticiones simultáneas', () => {
    storage.save({ access: 'expired', refresh: 'refresh' });
    http.get('/api/one/').subscribe();
    http.get('/api/two/').subscribe();
    requests.expectOne('/api/one/').flush({}, { status: 401, statusText: 'Unauthorized' });
    requests.expectOne('/api/two/').flush({}, { status: 401, statusText: 'Unauthorized' });
    requests.expectOne('/api/auth/refresh/').flush({ access: 'new' });
    requests.expectOne('/api/one/').flush({});
    requests.expectOne('/api/two/').flush({});
  });

  it('refresh inválido limpia la sesión y no crea un ciclo', () => {
    storage.save({ access: 'expired', refresh: 'invalid' });
    auth.restoreSession().subscribe((result) => expect(result).toBeNull());
    requests.expectOne('/api/auth/me/').flush({}, { status: 401, statusText: 'Unauthorized' });
    requests.expectOne('/api/auth/refresh/').flush({}, { status: 401, statusText: 'Unauthorized' });
    requests.expectNone('/api/auth/refresh/');
    expect(storage.refresh).toBeNull();
    expect(navigate).toHaveBeenCalledWith('/login');
  });

  it('si el reintento vuelve a fallar no renueva por segunda vez', () => {
    storage.save({ access: 'expired', refresh: 'refresh' });
    auth.restoreSession().subscribe();
    requests.expectOne('/api/auth/me/').flush({}, { status: 401, statusText: 'Unauthorized' });
    requests.expectOne('/api/auth/refresh/').flush({ access: 'new' });
    requests.expectOne('/api/auth/me/').flush({}, { status: 401, statusText: 'Unauthorized' });
    requests.expectNone('/api/auth/refresh/');
    expect(storage.access).toBeNull();
  });

  it('no comparte tokens con otras direcciones', () => {
    storage.save({ access: 'private-access', refresh: 'refresh' });
    for (const url of ['https://external.example/api/me/', '/api-other/']) {
      http.get(url).subscribe();
      const request = requests.expectOne(url);
      expect(request.request.headers.has('Authorization')).toBe(false);
      request.flush({});
    }
  });

  it('una respuesta tardía no restaura una sesión cerrada', () => {
    storage.save({ access: 'access', refresh: 'refresh' });
    auth.restoreSession().subscribe((result) => expect(result).toBeNull());
    const pending = requests.expectOne('/api/auth/me/');
    auth.logout();
    pending.flush(user);
    expect(auth.user()).toBeNull();
    expect(storage.access).toBeNull();
  });

  it('un refresh tardío no guarda tokens después del logout', () => {
    storage.save({ access: 'expired', refresh: 'refresh' });
    auth.refreshAccess().subscribe({ error: () => undefined });
    const pending = requests.expectOne('/api/auth/refresh/');
    auth.logout();
    pending.flush({ access: 'late' });
    expect(storage.access).toBeNull();
  });

  it('rechaza una dirección de panel ajena al rol recibido', () => {
    storage.save({ access: 'access', refresh: 'refresh' });
    auth.restoreSession().subscribe((result) => expect(result).toBeNull());
    requests.expectOne('/api/auth/me/').flush({ ...user, dashboard_path: '/dashboard/admin' });
    expect(auth.user()).toBeNull();
    expect(storage.access).toBeNull();
  });
});
