import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { API_URL } from '../../../../core/auth/api-url';
import { Instruments } from './instruments';
import { Instrument } from './instruments.models';
import { SUPERADMIN_ROUTES } from '../../superadmin.routes';

const base = '/api/superadmin/instruments/';
const item: Instrument = {
  id: 3,
  codigo: 'TEST-A',
  nombre: 'Instrumento ficticio',
  version: '1.0',
  descripcion: 'Descripción',
  instrucciones: 'Primera línea\nSegunda línea',
  es_inicial: true,
  activo: true,
  creado_en: '2026-09-21T10:00:00Z',
  actualizado_en: '2026-09-21T10:00:00Z',
};
const page = (results = [item], count = results.length, page = 1) => ({
  results,
  count,
  page,
  page_size: 20,
});

describe('Instrumentos T25-A', () => {
  let http: HttpTestingController;
  let fixture: ComponentFixture<Instruments>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: '/api' },
      ],
    });
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(Instruments);
    fixture.detectChanges();
    // jsdom no presenta ventanas: simula solo el ciclo nativo de apertura/cierre.
    dialog().showModal = vi.fn(function (this: HTMLDialogElement) {
      this.open = true;
    });
    dialog().close = vi.fn(function (this: HTMLDialogElement) {
      this.open = false;
    });
  });
  afterEach(() => {
    http.verify();
    vi.restoreAllMocks();
  });

  function load(results = [item]) {
    const request = http.expectOne((r) => r.url === base);
    request.flush(page(results));
    fixture.detectChanges();
    return request;
  }
  function button(text: string): HTMLButtonElement {
    return Array.from(
      fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>,
    ).find((button) => button.textContent?.trim() === text)!;
  }
  function dialog(): HTMLDialogElement {
    return fixture.nativeElement.querySelector('dialog');
  }
  function input(name: string, value: string) {
    const el = fixture.nativeElement.querySelector(
      `[formcontrolname="${name}"]`,
    ) as HTMLInputElement;
    el.value = value;
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }
  function submit() {
    dialog()
      .querySelector('form')!
      .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  }

  it('lista metadatos y publica una sola ruta protegida por el padre Superadmin', () => {
    load();
    expect(fixture.nativeElement.textContent).toContain('Instrumento ficticio');
    expect(fixture.nativeElement.textContent).toContain('TEST-A');
    expect(button('Ver')).toBeTruthy();
    expect(button('Editar')).toBeTruthy();
    expect(button('Desactivar')).toBeTruthy();
    expect(button('Eliminar')).toBeUndefined();
    expect(SUPERADMIN_ROUTES.filter((r) => r.path === 'evaluaciones/instrumentos')).toHaveLength(1);
  });
  it('aplica búsqueda y filtros con paginación conservando los filtros aplicados', () => {
    load();
    const vm = fixture.componentInstance.vm;
    vm.filters.patchValue({ search: ' TEST ', activo: 'false', es_inicial: 'true' });
    vm.search();
    const filtered = http.expectOne((r) => r.url === base);
    expect(filtered.request.params.get('search')).toBe('TEST');
    expect(filtered.request.params.get('activo')).toBe('false');
    expect(filtered.request.params.get('es_inicial')).toBe('true');
    expect(filtered.request.params.get('page')).toBe('1');
    filtered.flush(page([item], 21));
    vm.filters.controls.search.setValue('sin aplicar');
    vm.goTo(2);
    const second = http.expectOne((r) => r.url === base);
    expect(second.request.params.get('search')).toBe('TEST');
    expect(second.request.params.get('page')).toBe('2');
    second.flush(page([item], 21, 2));
  });
  it('crea desde el modal, impide doble envío y recarga al guardar', async () => {
    load([]);
    const trigger = button('Nuevo instrumento');
    trigger.focus();
    trigger.click();
    await fixture.whenStable();
    expect(dialog().open).toBe(true);
    input('codigo', '  TEST-B ');
    input('nombre', 'Nuevo instrumento de prueba');
    submit();
    submit();
    const request = http.expectOne(base);
    expect(request.request.method).toBe('POST');
    expect(request.request.body.codigo).toBe('TEST-B');
    expect(request.request.body.version).toBe('1.0');
    for (const key of ['id', 'activo', 'creado_en', 'actualizado_en'])
      expect(request.request.body).not.toHaveProperty(key);
    fixture.componentInstance.close();
    expect(fixture.componentInstance.vm.mode()).toBe('create');
    request.flush(item);
    load();
    await fixture.whenStable();
    expect(dialog().open).toBe(false);
    expect(document.activeElement).toBe(trigger);
    expect(fixture.nativeElement.textContent).toContain('Instrumento guardado.');
  });
  it('bloquea campos vacíos, espacios y longitudes excesivas antes del HTTP', async () => {
    load();
    button('Nuevo instrumento').click();
    await fixture.whenStable();
    input('codigo', '   ');
    input('nombre', '');
    input('version', '');
    submit();
    await fixture.whenStable();
    http.expectNone(base);
    expect(dialog().textContent).toContain('Este campo es obligatorio');
    const vm = fixture.componentInstance.vm;
    vm.form.patchValue({
      codigo: 'x'.repeat(51),
      nombre: 'x'.repeat(201),
      version: 'x'.repeat(51),
    });
    vm.save();
    expect(vm.form.invalid).toBe(true);
    http.expectNone(base);
  });
  it('mantiene abierto el modal y muestra colisiones del backend junto a versión', async () => {
    load();
    button('Nuevo instrumento').click();
    await fixture.whenStable();
    input('codigo', 'TEST-A');
    input('nombre', 'Duplicado');
    submit();
    http
      .expectOne(base)
      .flush(
        { version: ['Ya existe un instrumento con este código y versión.'] },
        { status: 400, statusText: 'Bad Request' },
      );
    await fixture.whenStable();
    expect(dialog().open).toBe(true);
    expect(dialog().querySelector('#version-error')?.textContent).toContain('Ya existe');
    expect(fixture.componentInstance.vm.saving()).toBe(false);
    input('version', '2.0');
    expect(fixture.componentInstance.vm.form.controls.version.valid).toBe(true);
  });
  it('consulta detalle y pasa a edición en el mismo modal usando PATCH', async () => {
    load();
    button('Ver').click();
    http.expectOne(base + '3/').flush(item);
    await fixture.whenStable();
    expect(dialog().open).toBe(true);
    expect(dialog().textContent).toContain('Primera línea');
    expect(dialog().textContent).toContain('Descripción');
    button('Editar instrumento').click();
    http.expectOne(base + '3/').flush(item);
    await fixture.whenStable();
    input('nombre', 'Nombre editado');
    submit();
    const request = http.expectOne(base + '3/');
    expect(request.request.method).toBe('PATCH');
    expect(request.request.body.nombre).toBe('Nombre editado');
    expect(request.request.body.es_inicial).toBe(true);
    expect(request.request.body).not.toHaveProperty('activo');
    request.flush({ ...item, nombre: 'Nombre editado' });
    load();
    await fixture.whenStable();
    expect(dialog().open).toBe(false);
  });
  it('activa y desactiva mediante acciones sin DELETE, conservando filtros', () => {
    load();
    const vm = fixture.componentInstance.vm;
    vm.filters.controls.activo.setValue('true');
    vm.search();
    load();
    vm.toggle(item);
    vm.toggle(item);
    const request = http.expectOne(base + '3/deactivate/');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({});
    request.flush({ ...item, activo: false });
    const reload = load([]);
    expect(reload.request.params.get('activo')).toBe('true');
    vm.toggle({ ...item, activo: false });
    http.expectOne(base + '3/activate/').flush(item);
    load();
    expect(vm.notice()).toContain('activado');
  });
  it('recupera errores de listado, detalle y acción sin perder el registro', async () => {
    http.expectOne((r) => r.url === base).flush({}, { status: 500, statusText: 'Error' });
    await fixture.whenStable();
    expect(fixture.nativeElement.textContent).toContain('No se pudo completar');
    button('Reintentar').click();
    load();
    button('Ver').click();
    http.expectOne(base + '3/').flush({}, { status: 404, statusText: 'Not Found' });
    await fixture.whenStable();
    expect(dialog().textContent).toContain('no existe');
    fixture.componentInstance.close();
    await fixture.whenStable();
    fixture.componentInstance.vm.toggle(item);
    http.expectOne(base + '3/deactivate/').flush({}, { status: 403, statusText: 'Forbidden' });
    await fixture.whenStable();
    expect(fixture.componentInstance.vm.busy()).toBe(false);
    expect(fixture.nativeElement.textContent).toContain('No tienes acceso');
    expect(fixture.componentInstance.vm.page()?.results[0].activo).toBe(true);
  });
  it('cancela lecturas obsoletas al cerrar modal o reemplazar búsqueda', async () => {
    load();
    const vm = fixture.componentInstance.vm;
    vm.open('edit', item);
    const detail = http.expectOne(base + '3/');
    await fixture.whenStable();
    dialog().dispatchEvent(new Event('cancel', { cancelable: true }));
    expect(detail.cancelled).toBe(true);
    await fixture.whenStable();
    expect(dialog().open).toBe(false);
    vm.search();
    const old = http.expectOne((r) => r.url === base);
    vm.search();
    expect(old.cancelled).toBe(true);
    load();
  });
  it('retrocede de página si se desactiva el último resultado del filtro', async () => {
    load();
    const vm = fixture.componentInstance.vm;
    vm.goTo(2);
    http.expectOne((r) => r.url === base).flush(page([item], 21, 2));
    vm.toggle(item);
    http.expectOne(base + '3/deactivate/').flush({ ...item, activo: false });
    http.expectOne((r) => r.url === base).flush(page([], 20, 2));
    await fixture.whenStable();
    const request = http.expectOne((r) => r.url === base);
    expect(request.request.params.get('page')).toBe('1');
    request.flush(page([item], 20));
  });
});
