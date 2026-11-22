import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { API_URL } from '../../../../core/auth/api-url';
import { SUPERADMIN_ROUTES } from '../../superadmin.routes';
import { InstrumentContent } from './content';
import { ContentKind, ContentRow } from './content.models';

const base = '/api/superadmin/';
const instrument = {
  id: 'a1000000-0000-4000-8000-000000000001',
  codigo: 'TEST',
  nombre: 'Prueba',
  version: '1.0',
  activo: true,
};
const secondInstrument = {
  ...instrument,
  id: 'a1000000-0000-4000-8000-000000000002',
  version: '2.0',
};
const audit = {
  activo: true,
  creado_en: '2026-10-01T10:00:00Z',
  actualizado_en: '2026-10-01T10:00:00Z',
};
const scale: ContentRow = {
  ...audit,
  id: 'b1000000-0000-4000-8000-000000000001',
  nombre: 'Frecuencia',
  descripcion: 'Descripción de prueba',
};
const question: ContentRow = {
  ...audit,
  id: 'c1000000-0000-4000-8000-000000000001',
  instrumento_id: instrument.id,
  texto: 'Pregunta de prueba',
  orden: 1,
  tipo_respuesta: 'ESCALA',
  escala_id: scale.id,
  obligatoria: true,
  invertida: false,
};
const option: ContentRow = {
  ...audit,
  id: 'd1000000-0000-4000-8000-000000000001',
  escala_id: scale.id,
  etiqueta: 'Nunca',
  valor: 0,
  orden: 1,
};
const range: ContentRow = {
  ...audit,
  id: 'e1000000-0000-4000-8000-000000000001',
  instrumento_id: instrument.id,
  nombre: 'Inicial',
  puntaje_minimo: 0,
  puntaje_maximo: 10,
  orden: 1,
  interpretacion: 'Descripción del intervalo',
};
const page = (results: unknown[], count = results.length, index = 1) => ({
  results,
  count,
  page: index,
  page_size: 20,
});
const questionsPath = `${base}instruments/${instrument.id}/questions/`;
const rangesPath = `${base}instruments/${instrument.id}/ranges/`;
const optionsPath = `${base}scales/${scale.id}/options/`;

describe('Contenido de instrumentos T25', () => {
  let http: HttpTestingController;
  let fixture: ComponentFixture<InstrumentContent>;
  function setup(kind: ContentKind, query: Record<string, string> = {}) {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: '/api' },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { data: { kind }, queryParamMap: convertToParamMap(query) } },
        },
      ],
    });
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(InstrumentContent);
    fixture.detectChanges();
    const dialog = fixture.nativeElement.querySelector('dialog') as HTMLDialogElement;
    dialog.showModal = vi.fn(function (this: HTMLDialogElement) {
      this.open = true;
    });
    dialog.close = vi.fn(function (this: HTMLDialogElement) {
      this.open = false;
    });
    return fixture.componentInstance.vm;
  }
  function catalogs(kind: ContentKind, scales = [scale]) {
    http.expectOne(`${base}instruments/?page=1`).flush(page([instrument, secondInstrument]));
    if (kind === 'questions') http.expectOne(`${base}scales/?page=1`).flush(page(scales));
  }
  function load(path: string, rows: ContentRow[]) {
    const req = http.expectOne((request) => request.url === path);
    req.flush(page(rows));
    fixture.detectChanges();
    return req;
  }
  function button(label: string) {
    return Array.from(
      fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>,
    ).find((item) => item.textContent?.trim() === label)!;
  }
  afterEach(() => {
    http?.verify();
    vi.restoreAllMocks();
  });

  it('publica preguntas, escalas y rangos sin duplicar Instrumentos ni crear una pantalla de opciones', () => {
    setup('scales');
    load(base + 'scales/', []);
    for (const [path, kind] of [
      ['preguntas', 'questions'],
      ['escalas', 'scales'],
      ['rangos', 'ranges'],
    ]) {
      const routes = SUPERADMIN_ROUTES.filter((route) => route.path === `evaluaciones/${path}`);
      expect(routes).toHaveLength(1);
      expect(routes[0].data?.['kind']).toBe(kind);
    }
    expect(
      SUPERADMIN_ROUTES.filter((route) => route.path === 'evaluaciones/instrumentos'),
    ).toHaveLength(1);
    expect(SUPERADMIN_ROUTES.some((route) => route.path?.includes('opciones'))).toBe(false);
  });

  it('exige instrumento y usa su UUID string para listar preguntas', () => {
    const vm = setup('questions');
    catalogs('questions');
    expect(vm.canManage()).toBe(false);
    vm.open('create');
    expect(vm.mode()).toBeNull();
    const select: HTMLSelectElement = fixture.nativeElement.querySelector('.parent-picker select');
    fixture.detectChanges();
    select.value = instrument.id;
    select.dispatchEvent(new Event('change'));
    load(questionsPath, [question]);
    expect(vm.instrumentId()).toBe(instrument.id);
    expect(typeof vm.page()!.results[0].id).toBe('string');
    expect(fixture.nativeElement.textContent).toContain('Pregunta de prueba');
    expect(fixture.nativeElement.textContent).toContain('Frecuencia');
  });

  it('carga todas las páginas del selector y admite un instrumento fuera de la primera página', () => {
    const vm = setup('ranges', { instrumento: secondInstrument.id });
    http.expectOne(`${base}instruments/?page=1`).flush(page([instrument], 21));
    expect(vm.ready()).toBe(false);
    http.expectOne(`${base}instruments/?page=2`).flush(page([secondInstrument], 21, 2));
    load(`${base}instruments/${secondInstrument.id}/ranges/`, []);
    expect(vm.instruments().map((item) => item.id)).toEqual([instrument.id, secondInstrument.id]);
    expect(vm.instrumentId()).toBe(secondInstrument.id);
  });

  it('crea una pregunta con escala, propiedades y relación UUID desde el modal', async () => {
    const vm = setup('questions', { instrumento: instrument.id });
    catalogs('questions');
    load(questionsPath, []);
    button('Crear pregunta').click();
    await fixture.whenStable();
    expect(fixture.nativeElement.querySelector('dialog').open).toBe(true);
    const text: HTMLTextAreaElement = fixture.nativeElement.querySelector('dialog textarea');
    text.value = ' Nueva pregunta ';
    text.dispatchEvent(new Event('input'));
    vm.form.patchValue({
      tipo_respuesta: 'ESCALA',
      escala_id: scale.id,
      obligatoria: false,
      invertida: true,
    });
    fixture.nativeElement
      .querySelector('dialog form')
      .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    vm.save();
    const req = http.expectOne(questionsPath);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      texto: 'Nueva pregunta',
      orden: 1,
      tipo_respuesta: 'ESCALA',
      escala_id: scale.id,
      obligatoria: false,
      invertida: true,
    });
    expect(req.request.body).not.toHaveProperty('instrumento_id');
    expect(req.request.body).not.toHaveProperty('activo');
    vm.close();
    expect(vm.mode()).toBe('create');
    req.flush(question);
    load(questionsPath, [question]);
    await fixture.whenStable();
    expect(vm.mode()).toBeNull();
    expect(fixture.nativeElement.querySelector('dialog').open).toBe(false);
  });

  it('valida escala requerida, orden entero y texto antes de enviar preguntas', () => {
    const vm = setup('questions', { instrumento: instrument.id });
    catalogs('questions');
    load(questionsPath, []);
    vm.open('create');
    vm.form.patchValue({ texto: ' ', orden: 0, tipo_respuesta: 'ESCALA' });
    vm.save();
    expect(vm.form.invalid).toBe(true);
    expect(vm.form.hasError('scaleRequired')).toBe(true);
    vm.form.patchValue({ texto: 'Prueba', orden: 1.5, escala_id: scale.id });
    vm.save();
    expect(vm.form.get('orden')?.invalid).toBe(true);
    http.expectNone(questionsPath);
  });

  it('edita una pregunta y limpia su escala al cambiar el tipo', () => {
    const vm = setup('questions', { instrumento: instrument.id });
    catalogs('questions');
    load(questionsPath, [question]);
    vm.open('edit', question);
    http.expectOne(questionsPath + question.id + '/').flush(question);
    vm.form.patchValue({ tipo_respuesta: 'BOOLEANO', texto: 'Editada' });
    vm.save();
    const req = http.expectOne(questionsPath + question.id + '/');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body.escala_id).toBeNull();
    expect(req.request.body.tipo_respuesta).toBe('BOOLEANO');
    req.flush({ ...question, tipo_respuesta: 'BOOLEANO', escala_id: null });
    load(questionsPath, []);
  });

  it('conserva una escala histórica inactiva pero no la ofrece para otra pregunta', () => {
    const vm = setup('questions', { instrumento: instrument.id });
    catalogs('questions', [{ ...scale, activo: false }]);
    load(questionsPath, [question]);
    vm.open('create');
    expect(vm.scaleAllowed({ ...scale, activo: false })).toBe(false);
    vm.open('edit', question);
    http.expectOne(questionsPath + question.id + '/').flush(question);
    expect(vm.scaleAllowed({ ...scale, activo: false })).toBe(true);
    expect(vm.form.get('escala_id')?.value).toBe(scale.id);
  });

  it('cancela detalles y listas antiguos al cambiar de instrumento', async () => {
    const vm = setup('questions', { instrumento: instrument.id });
    catalogs('questions');
    load(questionsPath, [question]);
    vm.open('detail', question);
    const detail = http.expectOne(questionsPath + question.id + '/');
    vm.chooseInstrument(secondInstrument.id);
    expect(detail.cancelled).toBe(true);
    expect(vm.mode()).toBeNull();
    const old = http.expectOne(
      (r) => r.url === `${base}instruments/${secondInstrument.id}/questions/`,
    );
    vm.chooseInstrument(instrument.id);
    expect(old.cancelled).toBe(true);
    load(questionsPath, [question]);
    await fixture.whenStable();
    expect(vm.instrumentId()).toBe(instrument.id);
  });

  it('crea, consulta y edita escalas desde modales y conserva el UUID', async () => {
    const vm = setup('scales');
    load(base + 'scales/', []);
    vm.open('create');
    vm.form.patchValue({ nombre: ' Frecuencia ', descripcion: 'Texto' });
    vm.save();
    const create = http.expectOne(base + 'scales/');
    expect(create.request.body).toEqual({ nombre: 'Frecuencia', descripcion: 'Texto' });
    create.flush(scale);
    load(base + 'scales/', [scale]);
    button('Ver').click();
    http.expectOne(`${base}scales/${scale.id}/`).flush(scale);
    await fixture.whenStable();
    expect(fixture.nativeElement.querySelector('dialog').textContent).toContain(
      'Descripción de prueba',
    );
    button('Editar escala').click();
    http.expectOne(`${base}scales/${scale.id}/`).flush(scale);
    vm.form.patchValue({ nombre: 'Frecuencia editada' });
    vm.save();
    const edit = http.expectOne(`${base}scales/${scale.id}/`);
    expect(edit.request.method).toBe('PATCH');
    edit.flush({ ...scale, nombre: 'Frecuencia editada' });
    load(base + 'scales/', [scale]);
  });

  it('administra opciones dentro de la escala seleccionada y vuelve al listado', () => {
    const vm = setup('scales');
    load(base + 'scales/', [scale]);
    button('Opciones').click();
    load(optionsPath, [option]);
    expect(vm.kind()).toBe('options');
    expect(vm.scope().parentId).toBe(scale.id);
    expect(fixture.nativeElement.textContent).toContain('Frecuencia');
    vm.open('create');
    vm.form.patchValue({ etiqueta: 'Siempre', valor: 5, orden: 2 });
    vm.save();
    const create = http.expectOne(optionsPath);
    expect(create.request.body).toEqual({ etiqueta: 'Siempre', valor: 5, orden: 2 });
    expect(create.request.body).not.toHaveProperty('pregunta_id');
    create.flush(option);
    load(optionsPath, [option]);
    vm.backToScales();
    load(base + 'scales/', [scale]);
    expect(vm.kind()).toBe('scales');
    expect(vm.scale()).toBeNull();
  });

  it('edita valor, etiqueta y orden de una opción sin cambiar de escala', () => {
    const vm = setup('scales');
    load(base + 'scales/', [scale]);
    vm.openOptions(scale);
    load(optionsPath, [option]);
    vm.open('edit', option);
    http.expectOne(optionsPath + option.id + '/').flush(option);
    vm.form.patchValue({ etiqueta: 'Casi nunca', valor: -1, orden: 3 });
    vm.save();
    const req = http.expectOne(optionsPath + option.id + '/');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ etiqueta: 'Casi nunca', valor: -1, orden: 3 });
    req.flush(option);
    load(optionsPath, [option]);
  });

  it('valida rangos y envía mínimos/máximos al instrumento seleccionado', () => {
    const vm = setup('ranges', { instrumento: instrument.id });
    catalogs('ranges');
    load(rangesPath, []);
    vm.open('create');
    vm.form.patchValue({ nombre: 'Inicial', puntaje_minimo: 10, puntaje_maximo: 5 });
    vm.save();
    expect(vm.form.hasError('range')).toBe(true);
    http.expectNone(rangesPath);
    vm.form.patchValue({ puntaje_minimo: 0, interpretacion: 'Descripción' });
    vm.save();
    const req = http.expectOne(rangesPath);
    expect(req.request.body).toEqual({
      nombre: 'Inicial',
      orden: 1,
      puntaje_minimo: 0,
      puntaje_maximo: 5,
      interpretacion: 'Descripción',
    });
    req.flush(range);
    load(rangesPath, [range]);
    vm.open('edit', range);
    http.expectOne(rangesPath + range.id + '/').flush(range);
    vm.form.patchValue({ puntaje_maximo: 20 });
    vm.save();
    const edit = http.expectOne(rangesPath + range.id + '/');
    expect(edit.request.method).toBe('PATCH');
    edit.flush({ ...range, puntaje_maximo: 20 });
    load(rangesPath, [range]);
  });

  for (const kind of ['questions', 'scales', 'options', 'ranges'] as const) {
    it(`activa/desactiva ${kind} sin DELETE y recarga los filtros`, () => {
      const vm = setup(kind === 'options' ? 'scales' : kind, { instrumento: instrument.id });
      if (kind === 'questions' || kind === 'ranges') catalogs(kind);
      const path = {
        questions: questionsPath,
        scales: base + 'scales/',
        options: optionsPath,
        ranges: rangesPath,
      }[kind];
      const row = { questions: question, scales: scale, options: option, ranges: range }[kind];
      if (kind === 'options') {
        load(base + 'scales/', [scale]);
        vm.openOptions(scale);
      }
      load(path, [row]);
      vm.toggle(row);
      vm.toggle(row);
      const deactivate = http.expectOne(path + row.id + '/deactivate/');
      expect(deactivate.request.method).toBe('POST');
      expect(deactivate.request.body).toEqual({});
      deactivate.flush({ ...row, activo: false });
      load(path, [{ ...row, activo: false }]);
      vm.toggle({ ...row, activo: false });
      http.expectOne(path + row.id + '/activate/').flush(row);
      load(path, [row]);
    });
  }

  for (const kind of ['questions', 'options'] as const) {
    it(`ordena ${kind} mediante acción explícita y conserva identidades`, () => {
      const vm = setup(kind === 'options' ? 'scales' : kind, { instrumento: instrument.id });
      const row = kind === 'questions' ? question : option;
      const path = kind === 'questions' ? questionsPath : optionsPath;
      if (kind === 'questions') catalogs(kind);
      else {
        load(base + 'scales/', [scale]);
        vm.openOptions(scale);
      }
      load(path, [row]);
      vm.move(row, 'down');
      const req = http.expectOne(path + row.id + '/move/');
      expect(req.request.body).toEqual({ direction: 'down' });
      req.flush({ ...row, orden: 2 });
      load(path, [{ ...row, orden: 2 }]);
      expect(vm.page()?.results[0].id).toBe(row.id);
    });
  }

  it('muestra errores por campo, conserva el modal y permite corregir duplicados', async () => {
    const vm = setup('scales');
    load(base + 'scales/', []);
    vm.open('create');
    vm.form.patchValue({ nombre: 'Duplicada' });
    vm.save();
    http
      .expectOne(base + 'scales/')
      .flush({ nombre: ['Ya existe una escala.'] }, { status: 400, statusText: 'Bad Request' });
    await fixture.whenStable();
    expect(vm.mode()).toBe('create');
    expect(vm.saving()).toBe(false);
    expect(fixture.nativeElement.querySelector('dialog').textContent).toContain(
      'Ya existe una escala',
    );
    vm.form.patchValue({ nombre: 'Otra' });
    expect(vm.form.valid).toBe(true);
  });

  it('cancela con Escape y recupera errores de detalle sin guardar un registro equivocado', async () => {
    const vm = setup('scales');
    load(base + 'scales/', [scale]);
    vm.open('edit', scale);
    http
      .expectOne(`${base}scales/${scale.id}/`)
      .flush({}, { status: 404, statusText: 'Not Found' });
    vm.save();
    expect(vm.selected()).toBeNull();
    await fixture.whenStable();
    fixture.nativeElement
      .querySelector('dialog')
      .dispatchEvent(new Event('cancel', { cancelable: true }));
    expect(vm.mode()).toBeNull();
  });

  it('aplica filtros, cancela lecturas viejas y conserva búsqueda al paginar', () => {
    const vm = setup('scales');
    const old = http.expectOne((r) => r.url === base + 'scales/');
    vm.filters.patchValue({ search: ' Frecuencia ', activo: 'false' });
    vm.search();
    expect(old.cancelled).toBe(true);
    const req = http.expectOne((r) => r.url === base + 'scales/');
    expect(req.request.params.get('search')).toBe('Frecuencia');
    expect(req.request.params.get('activo')).toBe('false');
    req.flush(page([scale], 21));
    vm.goTo(2);
    const next = http.expectOne((r) => r.url === base + 'scales/');
    expect(next.request.params.get('page')).toBe('2');
    expect(next.request.params.get('search')).toBe('Frecuencia');
    next.flush(page([scale], 21, 2));
  });

  it('recupera fallos de catálogos y de listado sin ofrecer escrituras prematuras', () => {
    const vm = setup('ranges');
    http.expectOne(`${base}instruments/?page=1`).flush({}, { status: 500, statusText: 'Error' });
    expect(vm.canManage()).toBe(false);
    expect(vm.catalogError()).toBeTruthy();
    vm.loadCatalogs();
    catalogs('ranges');
    vm.chooseInstrument(instrument.id);
    http.expectOne((r) => r.url === rangesPath).flush({}, { status: 500, statusText: 'Error' });
    expect(vm.page()).toBeNull();
    expect(vm.error()).toBeTruthy();
    vm.reload();
    load(rangesPath, [range]);
    expect(vm.error()).toBe('');
  });
});
