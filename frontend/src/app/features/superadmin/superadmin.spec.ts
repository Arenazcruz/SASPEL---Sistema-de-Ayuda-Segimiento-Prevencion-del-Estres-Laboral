/**
 * Pruebas con HTTP y navegación simulados del módulo administrativo: carga de datos,
 * formularios, filtros, permisos de rutas y acciones. Los escenarios it describen lo que se
 * protege; no escriben en PostgreSQL.
 */
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import {
  ActivatedRoute,
  ActivatedRouteSnapshot,
  convertToParamMap,
  provideRouter,
  Router,
  RouterStateSnapshot,
  UrlTree,
} from '@angular/router';
import { BehaviorSubject, of } from 'rxjs';
import { AuthService } from '../../core/auth/auth.service';
import { API_URL } from '../../core/auth/api-url';
import { FunctionalRole, ROLE_DASHBOARDS } from '../../core/auth/auth.models';
import { SuperadminLayout } from './layout/superadmin-layout';
import { SuperadminService } from './superadmin.service';
import { Person } from './superadmin.models';
import { UserForm } from './users/user-form';
import { UserList } from './users/user-list';
import { UserPassword } from './users/user-password';
import { superadminChildGuard } from './superadmin.routes';

const person: Person = {
  id: 2,
  email: 'ana@example.com',
  first_name: 'Ana',
  last_name: 'Prueba',
  nombre_completo: 'Ana Prueba',
  role: 'NUEVO_TRABAJADOR',
  is_active: true,
  fecha_registro: '2026-09-01T12:00:00Z',
  last_login: null,
  codigo_empleado: 'SA-TEST',
  apellido_materno: '',
  nombre_preferido: '',
  fecha_nacimiento: null,
  sexo: '',
  telefono: '',
  area: null,
  cargo: null,
  tamizaje_resuelto: false,
  habilitado_asignaciones: false,
  tiene_perfil: true,
};
const authUser = signal({
  id: 1,
  email: 'root@example.com',
  first_name: 'Root',
  role: 'SUPERADMIN' as FunctionalRole,
  dashboard_path: '/dashboard/superadmin',
});
const routeData = new BehaviorSubject({});
const query = new BehaviorSubject(convertToParamMap({}));

function setup(component: unknown, id?: number) {
  routeData.next({});
  query.next(convertToParamMap({}));
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      provideHttpClient(),
      provideHttpClientTesting(),
      { provide: API_URL, useValue: '/api' },
      { provide: AuthService, useValue: { user: authUser, logout: vi.fn() } },
      {
        provide: ActivatedRoute,
        useValue: {
          snapshot: {
            paramMap: convertToParamMap(id ? { id } : {}),
            queryParamMap: convertToParamMap({}),
            data: {},
          },
          data: routeData,
          queryParamMap: query,
        },
      },
    ],
  });
  return TestBed.inject(HttpTestingController);
}
function catalogs(http: HttpTestingController, active = false) {
  for (const kind of ['areas', 'cargos'])
    http
      .expectOne(`/api/superadmin/${kind}/${active ? '?active=true' : ''}`)
      .flush([{ id: 1, nombre: kind, descripcion: '', activo: true }]);
}

describe('Superadmin layout y permisos', () => {
  beforeEach(() => {
    setup(SuperadminLayout);
    authUser.set({ ...authUser(), role: 'SUPERADMIN', dashboard_path: '/dashboard/superadmin' });
  });
  it('muestra funciones y abre/cierra submenús y menú móvil', async () => {
    const fixture = TestBed.createComponent(SuperadminLayout);
    await fixture.whenStable();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Usuarios');
    expect(
      el.querySelector('a[href="/dashboard/superadmin/personas/asignaciones-profesionales"]')
        ?.textContent,
    ).toContain('Asignaciones profesionales');
    expect(el.textContent).not.toContain('auth_user');
    el.querySelector<HTMLButtonElement>('[aria-controls="people-menu"]')!.click();
    await fixture.whenStable();
    expect(el.querySelector('#people-menu')).toBeNull();
    el.querySelector<HTMLButtonElement>('[aria-controls="people-menu"]')!.click();
    el.querySelector<HTMLButtonElement>('.mobile-toggle')!.click();
    await fixture.whenStable();
    expect(el.querySelector('.sidebar.open')).not.toBeNull();
    el.querySelector<HTMLButtonElement>('.backdrop')!.click();
    el.querySelector<HTMLButtonElement>('.desktop-toggle')!.click();
    await fixture.whenStable();
    expect(el.querySelector('.sa-shell.collapsed')).not.toBeNull();
  });
  for (const role of Object.keys(ROLE_DASHBOARDS) as FunctionalRole[]) {
    it(`protege rutas hijas frente a ${role}`, () => {
      authUser.set({ ...authUser(), role, dashboard_path: ROLE_DASHBOARDS[role] });
      const result = TestBed.runInInjectionContext(() =>
        superadminChildGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
      );
      if (role === 'SUPERADMIN') expect(result).toBe(true);
      else
        expect(TestBed.inject(Router).serializeUrl(result as UrlTree)).toBe(ROLE_DASHBOARDS[role]);
    });
  }
});

describe('Formulario de personas', () => {
  let http: HttpTestingController;
  afterEach(() => http.verify());
  function form(id?: number) {
    http = setup(UserForm, id);
    const fixture = TestBed.createComponent(UserForm);
    catalogs(http, true);
    if (id) http.expectOne(`/api/superadmin/users/${id}/`).flush(person);
    return fixture;
  }
  function fill(vm: UserForm['vm']) {
    vm.form.patchValue({
      ...person,
      role: 'NUEVO_TRABAJADOR',
      fecha_nacimiento: '',
      password: 'Clave-segura-528!',
      password_confirmation: 'Clave-segura-528!',
    });
  }
  it('valida obligatorios, fuerza de clave y coincidencia antes del envío', async () => {
    const fixture = form();
    const vm = fixture.componentInstance.vm;
    vm.submit();
    expect(vm.form.invalid).toBe(true);
    fill(vm);
    vm.form.controls.password.setValue('abcdefghi');
    vm.submit();
    expect(vm.form.controls.password.invalid).toBe(true);
    vm.form.controls.password.setValue('Valida-78564');
    vm.submit();
    expect(vm.form.hasError('passwordsMatch')).toBe(true);
    await fixture.whenStable();
    expect(fixture.nativeElement.textContent).toContain('Las contraseñas no coinciden.');
    http.expectNone('/api/superadmin/users/');
  });
  it('crea con datos reales, limpia claves y navega al detalle', () => {
    const fixture = form();
    const vm = fixture.componentInstance.vm;
    fill(vm);
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    vm.submit();
    const req = http.expectOne('/api/superadmin/users/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body.role).toBe('NUEVO_TRABAJADOR');
    expect(req.request.body).not.toHaveProperty('tamizaje_resuelto');
    req.flush(person);
    expect(vm.form.controls.password.value).toBe('');
    expect(navigate).toHaveBeenCalled();
  });
  it('exige confirmación adicional para crear Superadmin', () => {
    const vm = form().componentInstance.vm;
    fill(vm);
    vm.form.controls.role.setValue('SUPERADMIN');
    vm.submit();
    http.expectNone('/api/superadmin/users/');
    expect(vm.error()).toContain('Confirma');
  });
  // La edición personal usa PATCH; clave, rol y estado deben conservar sus acciones dedicadas.
  it('edita sin enviar contraseña, rol ni estado', () => {
    const vm = form(2).componentInstance.vm;
    vi.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    vm.form.controls.first_name.setValue('Editada');
    vm.submit();
    const req = http.expectOne('/api/superadmin/users/2/');
    expect(req.request.method).toBe('PATCH');
    for (const key of ['password', 'password_confirmation', 'role', 'is_active'])
      expect(req.request.body).not.toHaveProperty(key);
    req.flush({ ...person, first_name: 'Editada' });
  });
});

describe('Listado y estado', () => {
  let http: HttpTestingController;
  beforeEach(() => {
    http = setup(UserList);
  });
  afterEach(() => {
    http.verify();
    vi.restoreAllMocks();
  });
  it('presenta usuarios y solicita filtro de rol con la misma API', async () => {
    routeData.next({ filterRole: 'PSICOLOGO', title: 'Psicólogos' });
    const fixture = TestBed.createComponent(UserList);
    catalogs(http);
    const req = http.expectOne(
      (r) => r.url === '/api/superadmin/users/' && r.params.get('role') === 'PSICOLOGO',
    );
    req.flush({ count: 1, page: 1, page_size: 20, results: [{ ...person, role: 'PSICOLOGO' }] });
    await fixture.whenStable();
    expect(fixture.nativeElement.textContent).toContain('Ana Prueba');
    expect(fixture.nativeElement.textContent).toContain('Psicólogos');
    query.next(convertToParamMap({ page: 2, search: 'Ana' }));
    const second = http.expectOne(
      (r) => r.params.get('page') === '2' && r.params.get('search') === 'Ana',
    );
    second.flush({ count: 1, page: 2, page_size: 20, results: [] });
  });
  // Simulamos confirmación y respuesta HTTP para comprobar acción explícita y recarga.
  it('activa/desactiva mediante acción explícita y refresca el listado', () => {
    const vm = TestBed.createComponent(UserList).componentInstance.vm;
    catalogs(http);
    http
      .expectOne('/api/superadmin/users/?page=1')
      .flush({ count: 1, page: 1, page_size: 20, results: [person] });
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    for (const active of [true, false]) {
      vm.toggle({ ...person, is_active: active });
      const req = http.expectOne(`/api/superadmin/users/2/${active ? 'deactivate' : 'activate'}/`);
      expect(req.request.method).toBe('POST');
      req.flush({ ...person, is_active: !active });
      http
        .expectOne('/api/superadmin/users/?page=1')
        .flush({ count: 1, page: 1, page_size: 20, results: [person] });
    }
  });
});

describe('Restablecer contraseña', () => {
  it('valida, permite mostrar/ocultar y limpia ambos campos al guardar', async () => {
    const http = setup(UserPassword, 2);
    const fixture = TestBed.createComponent(UserPassword);
    const vm = fixture.componentInstance.vm;
    http.expectOne('/api/superadmin/users/2/').flush(person);
    vm.form.setValue({ password: 'Nueva-segura-912!', password_confirmation: 'distinta' });
    vm.submit();
    http.expectNone('/api/superadmin/users/2/reset-password/');
    vm.form.controls.password_confirmation.setValue('Nueva-segura-912!');
    await fixture.whenStable();
    fixture.nativeElement.querySelector('.sa-plain').click();
    await fixture.whenStable();
    expect(fixture.nativeElement.querySelector('input').type).toBe('text');
    vm.submit();
    const req = http.expectOne('/api/superadmin/users/2/reset-password/');
    req.flush({ detail: 'Contraseña restablecida.' });
    expect(vm.form.controls.password.value).toBe('');
    expect(vm.notice()).toContain('correctamente');
    http.verify();
  });
});
