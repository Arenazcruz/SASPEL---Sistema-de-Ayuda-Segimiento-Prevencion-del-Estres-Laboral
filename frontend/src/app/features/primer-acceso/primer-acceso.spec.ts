import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, Routes } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { of } from 'rxjs';
import { routes } from '../../app.routes';
import { API_URL } from '../../core/auth/api-url';
import { AuthUser, PrimerAccesoEstado } from '../../core/auth/auth.models';
import { AuthService } from '../../core/auth/auth.service';
import { LoginComponent } from '../auth/login/login';
import { PrimerAccesoPassword } from './password';
import { PrimerAccesoPoliticas } from './politicas';
import { Politica } from './primer-acceso.service';

const passwordState: PrimerAccesoEstado = {
  debe_cambiar_password: true,
  politicas_pendientes: ['policy-1', 'policy-2'],
  completo: false,
  siguiente_ruta: '/primer-acceso/password',
};
const policyState: PrimerAccesoEstado = {
  ...passwordState,
  debe_cambiar_password: false,
  siguiente_ruta: '/primer-acceso/politicas',
};
const completeState: PrimerAccesoEstado = {
  debe_cambiar_password: false,
  politicas_pendientes: [],
  completo: true,
  siguiente_ruta: '/dashboard/admin',
};
const user: AuthUser = {
  id: '00000000-0000-0000-0000-000000000001',
  email: 'ana@saspel.com',
  first_name: 'Ana',
  last_name: 'Prueba',
  role: 'ADMIN',
  dashboard_path: '/dashboard/admin',
  primer_acceso: passwordState,
};
const policies: Politica[] = [1, 2].map((id) => ({
  id: `policy-${id}`,
  tipo: id === 1 ? 'TERMINOS_USO' : 'PRIVACIDAD_DATOS',
  titulo: `Documento de prueba ${id}`,
  version: '1',
  contenido: '<script>Texto de prueba</script>\nSegunda línea.',
  vigente_desde: '2026-01-01T00:00:00Z',
  obligatoria: true,
  activo: true,
}));

describe('Primer acceso: formularios y navegación', () => {
  let http: HttpTestingController;
  let navigate: ReturnType<typeof vi.spyOn>;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: '/api' },
        {
          provide: AuthService,
          useValue: {
            user: signal(user),
            logout: vi.fn(),
            login: vi.fn().mockReturnValue(of(user)),
          },
        },
      ],
    });
    http = TestBed.inject(HttpTestingController);
    navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
  });
  afterEach(() => {
    http.verify();
    vi.restoreAllMocks();
  });

  it('login navega al cambio obligatorio indicado por el backend', () => {
    const vm = TestBed.createComponent(LoginComponent).componentInstance.vm;
    vm.form.setValue({ email: user.email, password: 'Temporal-852!' });
    vm.submit();
    expect(navigate).toHaveBeenCalledWith('/primer-acceso/password');
    expect(vm.form.controls.password.value).toBe('');
  });

  it('contraseña exige fuerza y confirmación y muestra errores del servidor', async () => {
    const fixture = TestBed.createComponent(PrimerAccesoPassword);
    const vm = fixture.componentInstance.vm;
    vm.form.setValue({ password: 'weak', password_confirmation: 'other' });
    vm.submit();
    await fixture.whenStable();
    expect(fixture.nativeElement.textContent).toContain('al menos 8 caracteres');
    expect(fixture.nativeElement.textContent).toContain('Las contraseñas no coinciden');
    http.expectNone('/api/auth/primer-acceso/password/');
    vm.form.setValue({
      password: 'Nueva-personal-852!',
      password_confirmation: 'Nueva-personal-852!',
    });
    vm.submit();
    http
      .expectOne('/api/auth/primer-acceso/password/')
      .flush(
        { password: ['La contraseña es demasiado común.'] },
        { status: 400, statusText: 'Bad Request' },
      );
    await fixture.whenStable();
    expect(fixture.nativeElement.textContent).toContain('demasiado común');
    expect(vm.saving()).toBe(false);
    expect(navigate).not.toHaveBeenCalled();
    vm.form.controls.password.setValue('Corregida-personal-827!');
    expect(vm.form.controls.password.hasError('server')).toBe(false);
  });

  it('contraseña completada limpia los campos y redirige a políticas', () => {
    const vm = TestBed.createComponent(PrimerAccesoPassword).componentInstance.vm;
    expect(vm.form.getRawValue()).toEqual({ password: '', password_confirmation: '' });
    vm.form.setValue({
      password: 'Nueva-personal-852!',
      password_confirmation: 'Nueva-personal-852!',
    });
    vm.submit();
    vm.submit();
    const request = http.expectOne('/api/auth/primer-acceso/password/');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({
      password: 'Nueva-personal-852!',
      password_confirmation: 'Nueva-personal-852!',
    });
    request.flush(policyState);
    expect(navigate).toHaveBeenCalledWith('/primer-acceso/politicas');
    expect(vm.form.getRawValue()).toEqual({ password: '', password_confirmation: '' });
  });

  it('exige casillas explícitas para todos los documentos y luego navega al panel', async () => {
    const fixture = TestBed.createComponent(PrimerAccesoPoliticas);
    const vm = fixture.componentInstance.vm;
    http.expectOne('/api/auth/primer-acceso/politicas/').flush(policies);
    await fixture.whenStable();
    const element = fixture.nativeElement as HTMLElement;
    expect(element.querySelectorAll('article')).toHaveLength(2);
    expect(element.textContent).toContain('Versión 1');
    expect(element.textContent).toContain('<script>Texto de prueba</script>');
    expect(element.querySelector('script')).toBeNull();
    const submit = element.querySelector<HTMLButtonElement>('button.button')!;
    expect(submit.disabled).toBe(true);
    vm.submit();
    http.expectNone('/api/auth/primer-acceso/aceptar/');
    const checkboxes = element.querySelectorAll<HTMLInputElement>('input[type="checkbox"]');
    checkboxes[0].click();
    await fixture.whenStable();
    expect(submit.disabled).toBe(true);
    checkboxes[1].click();
    await fixture.whenStable();
    expect(submit.disabled).toBe(false);
    submit.click();
    vm.submit();
    const request = http.expectOne('/api/auth/primer-acceso/aceptar/');
    expect(request.request.body).toEqual({ politicas: ['policy-1', 'policy-2'] });
    request.flush(completeState);
    expect(navigate).toHaveBeenCalledWith('/dashboard/admin');
  });

  it('cargar no acepta y un fallo permite reintentar sin marcar casillas', async () => {
    const fixture = TestBed.createComponent(PrimerAccesoPoliticas);
    const vm = fixture.componentInstance.vm;
    http
      .expectOne('/api/auth/primer-acceso/politicas/')
      .flush({}, { status: 500, statusText: 'Error' });
    await fixture.whenStable();
    expect(fixture.nativeElement.textContent).toContain('No se pudieron cargar');
    expect(vm.canAccept()).toBe(false);
    vm.load();
    http.expectOne('/api/auth/primer-acceso/politicas/').flush(policies);
    expect(vm.selected().size).toBe(0);
    expect(vm.canAccept()).toBe(false);
    http.expectNone('/api/auth/primer-acceso/aceptar/');
  });

  it('una versión retirada exige volver a cargar y aceptar explícitamente la nueva', () => {
    const vm = TestBed.createComponent(PrimerAccesoPoliticas).componentInstance.vm;
    http.expectOne('/api/auth/primer-acceso/politicas/').flush(policies);
    policies.forEach((p) => vm.select(p.id, true));
    vm.submit();
    http
      .expectOne('/api/auth/primer-acceso/aceptar/')
      .flush({ politicas: ['Versiones cambiadas'] }, { status: 400, statusText: 'Bad Request' });
    expect(vm.error()).toContain('Las políticas cambiaron');
    expect(vm.canAccept()).toBe(false);
    expect(vm.selected().size).toBe(0);
    vm.load();
    http
      .expectOne('/api/auth/primer-acceso/politicas/')
      .flush([{ ...policies[0], id: 'version-2', version: '2' }]);
    expect(vm.canAccept()).toBe(false);
    expect(navigate).not.toHaveBeenCalled();
  });

  it('si otra política se publica al aceptar evita recargar la misma ruta en bucle', () => {
    const vm = TestBed.createComponent(PrimerAccesoPoliticas).componentInstance.vm;
    http.expectOne('/api/auth/primer-acceso/politicas/').flush(policies);
    policies.forEach((p) => vm.select(p.id, true));
    vm.submit();
    http
      .expectOne('/api/auth/primer-acceso/aceptar/')
      .flush({ ...policyState, politicas_pendientes: ['new-version'] });
    expect(vm.canAccept()).toBe(false);
    expect(vm.error()).toContain('nuevas políticas pendientes');
    expect(navigate).not.toHaveBeenCalled();
  });

  it('sin documentos pendientes confirma el estado sin enviar una aceptación vacía', () => {
    TestBed.createComponent(PrimerAccesoPoliticas);
    http.expectOne('/api/auth/primer-acceso/politicas/').flush([]);
    http.expectOne('/api/auth/primer-acceso/').flush(completeState);
    http.expectNone('/api/auth/primer-acceso/aceptar/');
    expect(navigate).toHaveBeenCalledWith('/dashboard/admin');
  });
});

@Component({ template: 'Página de prueba' })
class RouteProbe {}

// Conserva los guards/rutas reales; sustituye las vistas para aislar esta prueba de sus APIs.
function guardRoutes(items: Routes): Routes {
  return items.map(({ loadComponent, loadChildren, children, ...route }) => ({
    ...route,
    ...(loadComponent ? { component: RouteProbe } : {}),
    ...(children ? { children: guardRoutes(children) } : {}),
  }));
}

describe('Primer acceso: guards reales sin bucles', () => {
  let current: ReturnType<typeof signal<AuthUser | null>>;
  beforeEach(() => {
    current = signal<AuthUser | null>(user);
    TestBed.configureTestingModule({
      providers: [
        provideRouter(guardRoutes(routes)),
        { provide: AuthService, useValue: { user: current, restoreSession: () => of(current()) } },
      ],
    });
  });

  for (const path of [
    '/dashboard/nuevo-trabajador',
    '/dashboard/psicologo',
    '/dashboard/admin',
    '/dashboard/trabajador',
  ]) {
    it(`redirige acceso directo a ${path} al paso pendiente`, async () => {
      const harness = await RouterTestingHarness.create(path);
      expect(TestBed.inject(Router).url).toBe('/primer-acceso/password');
      await harness.navigateByUrl('/primer-acceso/politicas');
      expect(TestBed.inject(Router).url).toBe('/primer-acceso/password');
      current.set({ ...user, primer_acceso: policyState });
      await harness.navigateByUrl(path);
      expect(TestBed.inject(Router).url).toBe('/primer-acceso/politicas');
      await harness.navigateByUrl('/primer-acceso/password');
      expect(TestBed.inject(Router).url).toBe('/primer-acceso/politicas');
    });
  }

  it('al completar vuelve al dashboard y ya no permite entrar a los pasos', async () => {
    current.set({ ...user, primer_acceso: completeState });
    const harness = await RouterTestingHarness.create('/primer-acceso/politicas');
    expect(TestBed.inject(Router).url).toBe('/dashboard/admin');
    await harness.navigateByUrl('/primer-acceso/password');
    expect(TestBed.inject(Router).url).toBe('/dashboard/admin');
    await harness.navigateByUrl('/dashboard/trabajador');
    expect(TestBed.inject(Router).url).toBe('/dashboard/admin');
  });

  it('SUPERADMIN entra directamente a su dashboard y omite los pasos', async () => {
    current.set({
      ...user,
      role: 'SUPERADMIN',
      dashboard_path: '/dashboard/superadmin',
      primer_acceso: { ...completeState, siguiente_ruta: '/dashboard/superadmin' },
    });
    const harness = await RouterTestingHarness.create('/login');
    expect(TestBed.inject(Router).url).toBe('/dashboard/superadmin');
    await harness.navigateByUrl('/primer-acceso/password');
    expect(TestBed.inject(Router).url).toBe('/dashboard/superadmin');
  });

  it('sin autenticación no entra a ningún paso', async () => {
    current.set(null);
    const harness = await RouterTestingHarness.create('/primer-acceso/password');
    expect(TestBed.inject(Router).url).toBe('/login');
    await harness.navigateByUrl('/primer-acceso/politicas');
    expect(TestBed.inject(Router).url).toBe('/login');
  });

  it('una nueva versión vuelve a bloquear una sesión ya completada', async () => {
    current.set({ ...user, primer_acceso: completeState });
    const harness = await RouterTestingHarness.create('/dashboard/admin');
    expect(TestBed.inject(Router).url).toBe('/dashboard/admin');
    current.set({ ...user, primer_acceso: policyState });
    await harness.navigateByUrl('/dashboard/psicologo');
    expect(TestBed.inject(Router).url).toBe('/primer-acceso/politicas');
  });
});
