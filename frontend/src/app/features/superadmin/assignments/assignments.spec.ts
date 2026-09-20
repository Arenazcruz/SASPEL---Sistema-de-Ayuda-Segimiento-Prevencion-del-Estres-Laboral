/** T23: formularios reales, contratos HTTP, recargas y cancelación de lecturas obsoletas. */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { API_URL } from '../../../core/auth/api-url';
import { AssignmentPerson, ProfessionalAssignment } from './assignments.models';
import { ProfessionalAssignments } from './assignments';

const base = '/api/superadmin/assignments/';
const worker: AssignmentPerson = {
  id: 2,
  nombre_completo: 'Ana Prueba',
  email: 'ana@example.com',
  codigo_empleado: 'T23-2',
  role: 'TRABAJADOR',
  is_active: true,
  habilitado_asignaciones: false,
};
const psychologist: AssignmentPerson = {
  ...worker,
  id: 3,
  nombre_completo: 'Psicóloga Uno',
  email: 'psych-one@example.com',
  role: 'PSICOLOGO',
  habilitado_asignaciones: true,
};
const replacement: AssignmentPerson = {
  ...psychologist,
  id: 4,
  nombre_completo: 'Psicólogo Dos',
  email: 'psych-two@example.com',
};
const assignment: ProfessionalAssignment = {
  id: 10,
  trabajador: worker,
  psicologo: psychologist,
  estado: 'ACTIVA',
  fecha_asignacion: '2026-09-14T10:00:00Z',
  fecha_fin: null,
  motivo_fin: '',
};
const page = <T>(results: T[], count = results.length) => ({
  results,
  count,
  page: 1,
  page_size: 20,
});

describe('Asignaciones profesionales T23', () => {
  let http: HttpTestingController;
  let fixture: ComponentFixture<ProfessionalAssignments>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: '/api' },
      ],
    });
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(ProfessionalAssignments);
    fixture.detectChanges();
  });
  afterEach(() => http.verify());

  function queries() {
    return {
      rows: http.expectOne((r) => r.url === base),
      workers: http.expectOne((r) => r.url === base + 'unassigned-workers/'),
      loads: http.expectOne(base + 'psychologists/'),
    };
  }

  function load(rows = [assignment], workers = [worker]) {
    const requests = queries();
    requests.rows.flush(page(rows));
    requests.workers.flush(page(workers));
    requests.loads.flush([
      { psicologo: psychologist, trabajadores_activos: rows.length },
      { psicologo: replacement, trabajadores_activos: 0 },
    ]);
    fixture.detectChanges();
    return requests;
  }

  function button(text: string): HTMLButtonElement {
    return [
      ...(fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>),
    ].find((item) => item.textContent?.trim() === text)!;
  }

  it('presenta trabajador, psicólogo actual, carga y acciones de la asignación vigente', () => {
    const requests = load();
    expect(requests.rows.request.params.get('estado')).toBe('ACTIVA');
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Ana Prueba');
    expect(text).toContain('Psicóloga Uno');
    expect(text).toContain('Psicólogo actual');
    expect(text).toContain('Carga de psicólogos');
    expect(button('Reasignar')).toBeTruthy();
    expect(button('Finalizar')).toBeTruthy();
  });

  it('asigna mediante formulario, evita doble envío y actualiza pendientes y carga', async () => {
    load([], [worker]);
    button('Asignar').click();
    fixture.detectChanges();
    const select: HTMLSelectElement = fixture.nativeElement.querySelector(
      '[formcontrolname="psicologo_id"]',
    );
    select.selectedIndex = 1;
    select.dispatchEvent(new Event('change'));
    fixture.nativeElement
      .querySelector('.assignment-form')
      .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    fixture.componentInstance.vm.submit();
    const request = http.expectOne(base);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({
      trabajador_id: worker.id,
      psicologo_id: psychologist.id,
    });
    expect(fixture.componentInstance.vm.busy()).toBe(true);
    request.flush(assignment, { status: 201, statusText: 'Created' });
    load([assignment], []);
    await fixture.whenStable();
    expect(fixture.componentInstance.vm.workers()?.count).toBe(0);
    expect(fixture.componentInstance.vm.loads()[0].trabajadores_activos).toBe(1);
    expect(fixture.componentInstance.vm.selection()).toBeNull();
    expect(fixture.nativeElement.textContent).toContain('Asignación creada.');
  });

  it('requiere psicólogo antes de enviar el alta', () => {
    load([], [worker]);
    fixture.componentInstance.vm.open({ kind: 'assign', worker });
    fixture.componentInstance.vm.submit();
    http.expectNone(base);
    expect(fixture.componentInstance.vm.form.controls.psicologo_id.invalid).toBe(true);
  });

  it('reasigna a otro psicólogo con motivo y conserva el vínculo histórico recibido', () => {
    load();
    const vm = fixture.componentInstance.vm;
    vm.open({ kind: 'reassign', assignment });
    expect(vm.availablePsychologists().map((row) => row.psicologo.id)).toEqual([replacement.id]);
    vm.form.setValue({ psicologo_id: replacement.id, motivo_fin: ' Cambio de disponibilidad ' });
    vm.submit();
    const request = http.expectOne(base + '10/reassign/');
    expect(request.request.body).toEqual({
      psicologo_id: replacement.id,
      motivo_fin: 'Cambio de disponibilidad',
    });
    const next = { ...assignment, id: 11, psicologo: replacement };
    request.flush(next, { status: 201, statusText: 'Created' });
    load([next], []);
    vm.history(worker);
    const queriesForHistory = queries();
    expect(queriesForHistory.rows.request.params.get('trabajador_id')).toBe('2');
    expect(queriesForHistory.rows.request.params.has('estado')).toBe(false);
    queriesForHistory.rows.flush(
      page([
        next,
        {
          ...assignment,
          estado: 'REASIGNADA',
          fecha_fin: '2026-09-14T11:00:00Z',
          motivo_fin: 'Cambio de disponibilidad',
        },
      ]),
    );
    queriesForHistory.workers.flush(page([]));
    queriesForHistory.loads.flush([]);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Reasignada');
    expect(fixture.nativeElement.textContent).toContain('Cambio de disponibilidad');
    expect(fixture.nativeElement.querySelectorAll('tbody')[0].rows.length).toBe(2);
  });

  it('finaliza solo tras motivo y envía la identidad del vínculo que se está cerrando', () => {
    load();
    const vm = fixture.componentInstance.vm;
    vm.open({ kind: 'finish', assignment });
    vm.submit();
    http.expectNone(base + '10/finish/');
    vm.form.controls.motivo_fin.setValue('Cierre de acompañamiento');
    vm.submit();
    const request = http.expectOne(base + '10/finish/');
    expect(request.request.body).toEqual({ motivo_fin: 'Cierre de acompañamiento' });
    request.flush({ ...assignment, estado: 'FINALIZADA' });
    load([], [worker]);
    expect(vm.workers()?.results[0].id).toBe(worker.id);
    expect(vm.notice()).toContain('sin asignación activa');
  });

  it('conserva el formulario y muestra el rechazo del servidor sin anunciar éxito', () => {
    load();
    const vm = fixture.componentInstance.vm;
    vm.open({ kind: 'reassign', assignment });
    vm.form.setValue({ psicologo_id: replacement.id, motivo_fin: 'Cambio' });
    vm.submit();
    http
      .expectOne(base + '10/reassign/')
      .flush(
        { psicologo_id: ['El psicólogo ya no está habilitado.'] },
        { status: 400, statusText: 'Bad Request' },
      );
    fixture.detectChanges();
    expect(vm.busy()).toBe(false);
    expect(vm.selection()?.kind).toBe('reassign');
    expect(vm.form.controls.motivo_fin.value).toBe('Cambio');
    expect(vm.notice()).toBe('');
    expect(fixture.nativeElement.querySelector('[role="alert"]').textContent).toContain(
      'ya no está habilitado',
    );
  });

  it('cancela lecturas antiguas y mantiene filtros/paginación independientes', () => {
    const old = queries();
    const vm = fixture.componentInstance.vm;
    vm.filters.setValue({ estado: 'FINALIZADA', search: 'Ana' });
    vm.search();
    expect(old.rows.cancelled).toBe(true);
    expect(old.workers.cancelled).toBe(true);
    expect(old.loads.cancelled).toBe(true);
    const current = load([]);
    expect(current.rows.request.params.get('estado')).toBe('FINALIZADA');
    expect(current.rows.request.params.get('search')).toBe('Ana');
    vm.page(2, true);
    const paged = load([]);
    expect(paged.workers.request.params.get('page')).toBe('2');
    expect(paged.rows.request.params.get('page')).toBe('1');
  });

  it('recupera una carga fallida con reintento y no ofrece datos parciales', () => {
    const requests = queries();
    requests.rows.flush({ detail: 'Error temporal' }, { status: 500, statusText: 'Server Error' });
    expect(requests.workers.cancelled).toBe(true);
    expect(requests.loads.cancelled).toBe(true);
    fixture.detectChanges();
    expect(fixture.componentInstance.vm.rows()).toBeNull();
    expect(button('Reintentar carga')).toBeTruthy();
    button('Reintentar carga').click();
    load();
    expect(fixture.componentInstance.vm.loadError()).toBe('');
  });

  it('muestra ausencia de psicólogos y deshabilita asignar', () => {
    const requests = queries();
    requests.rows.flush(page([]));
    requests.workers.flush(page([worker]));
    requests.loads.flush([]);
    fixture.detectChanges();
    expect(button('Asignar').disabled).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('No hay psicólogos activos y habilitados');
  });

  it('el historial cerrado no ofrece finalizar ni reasignar', () => {
    load([{ ...assignment, estado: 'FINALIZADA', motivo_fin: 'Fin' }], []);
    expect(button('Finalizar')).toBeUndefined();
    expect(button('Reasignar')).toBeUndefined();
    expect(button('Ver historial')).toBeTruthy();
  });
});
