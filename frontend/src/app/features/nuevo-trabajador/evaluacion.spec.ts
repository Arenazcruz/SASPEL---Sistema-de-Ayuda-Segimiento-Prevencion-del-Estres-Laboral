import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter, Router } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { of } from 'rxjs';
import { routes } from '../../app.routes';
import { API_URL } from '../../core/auth/api-url';
import { authGuard } from '../../core/auth/auth.guard';
import { primerAccesoGuard } from '../../core/auth/primer-acceso.guard';
import { roleGuard } from '../../core/auth/role.guard';
import { AuthUser } from '../../core/auth/auth.models';
import { AuthService } from '../../core/auth/auth.service';
import { TokenStorageService } from '../../core/auth/token-storage.service';
import { NuevoTrabajadorDashboard } from './dashboard';
import { EvaluacionInicialComponent } from './evaluacion';
import { EvaluacionDetalle, PreguntaEvaluacion, ResultadoEvaluacion } from './evaluacion.models';

const id = '35560ef6-7b44-47d5-aed6-b9e2395a0301';
const optionId = '35560ef6-7b44-47d5-aed6-b9e2395a0401';
const URL = `/api/nuevo-trabajador/evaluaciones/${id}/`;
const PATH = `/dashboard/nuevo-trabajador/evaluacion/${id}`;
const user: AuthUser = {
  id: '35560ef6-7b44-47d5-aed6-b9e2395a0001',
  first_name: 'Ana',
  last_name: 'Prueba',
  email: 'ana@saspel.com',
  role: 'NUEVO_TRABAJADOR',
  dashboard_path: '/dashboard/nuevo-trabajador',
  primer_acceso: {
    completo: true,
    debe_cambiar_password: false,
    politicas_pendientes: [],
    siguiente_ruta: '/dashboard/nuevo-trabajador',
  },
};
function detalle(): EvaluacionDetalle {
  const kinds: PreguntaEvaluacion['tipo_respuesta'][] = ['ESCALA', 'TEXTO', 'NUMERO', 'BOOLEANO'];
  return {
    asignacion_id: id,
    instrumento_id: '35560ef6-7b44-47d5-aed6-b9e2395a0201',
    nombre: 'Instrumento sintético',
    version: '1.2',
    instrucciones: 'Instrucciones dinámicas de prueba.\nLee con atención.',
    estado_asignacion: 'EN_PROGRESO',
    aplicacion_id: '35560ef6-7b44-47d5-aed6-b9e2395a0501',
    estado_aplicacion: 'INICIADA',
    fecha_inicio: '2026-10-12T12:00:00Z',
    fecha_finalizacion: null,
    disponible: true,
    respuestas: [],
    preguntas: kinds.map((kind, i) => ({
      id: `35560ef6-7b44-47d5-aed6-b9e2395a010${i}`,
      texto: `Pregunta sintética ${kind}`,
      tipo_respuesta: kind,
      orden: i + 1,
      obligatoria: true,
      opciones: kind === 'ESCALA' ? [{ id: optionId, etiqueta: 'Etiqueta de prueba' }] : [],
    })),
  };
}
function respondido(): EvaluacionDetalle {
  const data = detalle();
  data.respuestas = data.preguntas.map((p, i) => ({
    pregunta_id: p.id,
    opcion_id: i === 0 ? optionId : null,
    valor_texto: i === 1 ? 'Mi texto' : null,
    valor_numerico: i === 2 ? '0.0000' : null,
    valor_booleano: i === 3 ? false : null,
  }));
  return data;
}
const worker: AuthUser = { ...user, role: 'TRABAJADOR', dashboard_path: '/dashboard/trabajador' };
function resultado(estado: 'ASIGNADO' | 'PENDIENTE' = 'PENDIENTE'): ResultadoEvaluacion {
  return {
    aplicacion_id: detalle().aplicacion_id!,
    instrumento_id: detalle().instrumento_id,
    nombre: detalle().nombre,
    version: detalle().version,
    fecha_calculo: '2026-10-12T12:00:00Z',
    puntaje_total: '20.0000',
    rango: 'MODERADO',
    interpretacion: 'Interpretación configurada.',
    tamizaje_resuelto: true,
    nuevo_rol: 'TRABAJADOR',
    dashboard_path: worker.dashboard_path,
    estado_asignacion_profesional: estado,
  };
}
function resumen(estado: 'PENDIENTE' | 'EN_PROGRESO' | 'COMPLETADA', available = true) {
  return {
    evaluacion_inicial: {
      estado,
      asignacion_id: id,
      instrumento_id: detalle().instrumento_id,
      nombre: detalle().nombre,
      version: '1.2',
      fecha_asignacion: null,
      fecha_limite: null,
      puede_iniciar: estado === 'PENDIENTE' && available,
    },
  };
}

describe('Formulario dinámico de evaluación', () => {
  let http: HttpTestingController;
  let fixture: ComponentFixture<EvaluacionInicialComponent>;
  let navigate: ReturnType<typeof vi.spyOn>;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: '/api' },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ asignacionId: id }) } },
        },
      ],
    });
    http = TestBed.inject(HttpTestingController);
    TestBed.inject(TokenStorageService).save({ access: 'access', refresh: 'refresh' });
    navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    fixture = TestBed.createComponent(EvaluacionInicialComponent);
  });
  afterEach(() => {
    http.verify();
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it('renderiza instrucciones y cuatro tipos dinámicos sin información de puntuación', async () => {
    http.expectOne(URL).flush(detalle());
    await fixture.whenStable();
    const element: HTMLElement = fixture.nativeElement;
    expect(element.textContent).toContain('Instrucciones dinámicas de prueba.');
    expect(element.textContent).toContain('Versión 1.2');
    expect(element.querySelectorAll('fieldset')).toHaveLength(4);
    expect(element.querySelectorAll('input[type=radio]')).toHaveLength(3);
    expect(element.querySelectorAll('textarea')).toHaveLength(1);
    expect(element.querySelectorAll('input[type=number]')).toHaveLength(1);
    expect(element.textContent).toContain('Etiqueta de prueba');
    for (const hidden of ['invertida', 'puntaje', 'BAJO', 'MODERADO', 'ALTO'])
      expect(element.textContent).not.toContain(hidden);
    const options = element.querySelectorAll('fieldset')[0];
    options.querySelector('input')!.click();
    await fixture.whenStable();
    expect(fixture.componentInstance.vm.respondidas()).toBe(1);
    expect(element.textContent).toContain('1 de 4 preguntas respondidas');
    expect(element.querySelector('progress')?.value).toBe(25);
  });

  it('guarda respuestas parciales sin exigir todas las obligatorias', async () => {
    http.expectOne(URL).flush(detalle());
    const vm = fixture.componentInstance.vm;
    vm.set(detalle().preguntas[1].id, 'Solo texto');
    vm.guardar();
    const request = http.expectOne(URL + 'respuestas/');
    expect(request.request.method).toBe('POST');
    expect(Object.keys(request.request.body)).toEqual(['respuestas']);
    expect(request.request.body.respuestas[1].valor_texto).toBe('Solo texto');
    const data = detalle();
    data.respuestas = [request.request.body.respuestas[1]];
    request.flush(data);
    await fixture.whenStable();
    expect(vm.respondidas()).toBe(1);
    expect(vm.dirty()).toBe(false);
    expect(fixture.nativeElement.textContent).toContain('Progreso guardado');
  });

  it('continúa con respuestas recuperadas, incluyendo cero y No', async () => {
    http.expectOne(URL).flush(respondido());
    await fixture.whenStable();
    expect(fixture.componentInstance.vm.respondidas()).toBe(4);
    expect(fixture.nativeElement.querySelector('textarea').value).toBe('Mi texto');
    expect(fixture.nativeElement.querySelector('input[type=number]').value).toBe('0.0000');
    expect(
      fixture.nativeElement.querySelectorAll('fieldset')[3].querySelectorAll('input')[1].checked,
    ).toBe(true);
  });

  it('indica las obligatorias pendientes y no envía finalizar', async () => {
    http.expectOne(URL).flush(detalle());
    fixture.componentInstance.vm.finalizar();
    await fixture.whenStable();
    expect(fixture.nativeElement.querySelectorAll('.missing')).toHaveLength(4);
    expect(fixture.nativeElement.textContent).toContain('Responde las preguntas obligatorias');
    http.expectNone(URL + 'finalizar/');
  });

  it('una respuesta opcional vacía no bloquea finalizar y envía las respuestas actuales', () => {
    const data = respondido();
    data.preguntas[1].obligatoria = false;
    data.respuestas.splice(1, 1);
    http.expectOne(URL).flush(data);
    fixture.componentInstance.vm.finalizar();
    const request = http.expectOne(URL + 'finalizar/');
    expect(request.request.body.respuestas[2].valor_numerico).toBe('0.0000');
    expect(request.request.body.respuestas[3].valor_booleano).toBe(false);
    request.flush(resultado());
    http.expectOne('/api/auth/me/').flush(worker);
    expect(navigate).not.toHaveBeenCalled();
    fixture.componentInstance.vm.continuar();
    expect(navigate).toHaveBeenCalledWith('/dashboard/trabajador');
  });

  for (const estado of ['ASIGNADO', 'PENDIENTE'] as const) {
    it(`muestra resultado orientativo y seguimiento ${estado}, refresca rol y evita doble clic`, async () => {
      const auth = TestBed.inject(AuthService);
      auth.restoreSession().subscribe();
      http.expectOne('/api/auth/me/').flush(user);
      http.expectOne(URL).flush(respondido());
      const vm = fixture.componentInstance.vm;
      vm.finalizar();
      vm.finalizar();
      http.expectOne(URL + 'finalizar/').flush(resultado(estado));
      expect(auth.user()).toBeNull();
      http.expectOne('/api/auth/me/').flush(worker);
      await fixture.whenStable();
      expect(auth.user()?.role).toBe('TRABAJADOR');
      expect(TestBed.inject(TokenStorageService).access).toBe('access');
      expect(TestBed.inject(TokenStorageService).refresh).toBe('refresh');
      const content = fixture.nativeElement.textContent;
      for (const text of [
        'Evaluación inicial completada',
        '20.0000',
        'MODERADO',
        'Interpretación configurada.',
        'orientativo',
        'SASPEL no sustituye un diagnóstico clínico',
        estado === 'ASIGNADO' ? 'Profesional asignado' : 'Asignación profesional pendiente',
        'Continuar a mi panel',
      ]) {
        expect(content).toContain(text);
      }
      expect(vm.editable()).toBe(false);
      vm.finalizar();
      http.expectNone(URL + 'finalizar/');
      http.expectNone('/api/nuevo-trabajador/dashboard/');
      const button = [...fixture.nativeElement.querySelectorAll('button')].find((b: any) =>
        b.textContent.includes('Continuar a mi panel'),
      ) as HTMLButtonElement;
      button.click();
      expect(navigate).toHaveBeenCalledWith('/dashboard/trabajador');
    });
  }

  it('permite reintentar identidad sin repetir finalización ni perder tokens ante error temporal', () => {
    http.expectOne(URL).flush(respondido());
    const vm = fixture.componentInstance.vm;
    vm.finalizar();
    http.expectOne(URL + 'finalizar/').flush({ ...resultado(), rango: null, interpretacion: '' });
    http.expectOne('/api/auth/me/').flush({}, { status: 503, statusText: 'Unavailable' });
    expect(vm.resultado()?.rango).toBeNull();
    expect(TestBed.inject(TokenStorageService).access).toBe('access');
    vm.continuar();
    http.expectOne('/api/auth/me/').flush(worker);
    expect(navigate).toHaveBeenCalledWith('/dashboard/trabajador');
    http.expectNone(URL + 'finalizar/');
  });

  it('no permite editar ni guardar después de finalizar', async () => {
    http
      .expectOne(URL)
      .flush({ ...respondido(), estado_aplicacion: 'FINALIZADA', estado_asignacion: 'COMPLETADA' });
    await fixture.whenStable();
    const vm = fixture.componentInstance.vm;
    expect(vm.editable()).toBe(false);
    const before = vm.valores();
    vm.set(detalle().preguntas[0].id, null);
    vm.guardar();
    vm.finalizar();
    expect(vm.valores()).toBe(before);
    expect(
      [...fixture.nativeElement.querySelectorAll('fieldset')].every(
        (field: HTMLFieldSetElement) => field.disabled,
      ),
    ).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('solo lectura');
    expect(fixture.nativeElement.textContent).not.toContain('Guardar progreso');
  });

  it('conserva cambios ante error de guardado y permite reintentar', () => {
    http.expectOne(URL).flush(detalle());
    const vm = fixture.componentInstance.vm;
    vm.set(detalle().preguntas[1].id, 'Conservar');
    vm.guardar();
    http.expectOne(URL + 'respuestas/').flush({}, { status: 500, statusText: 'Error' });
    expect(vm.valores()[detalle().preguntas[1].id]).toBe('Conservar');
    expect(vm.dirty()).toBe(true);
    expect(vm.saving()).toBe(false);
    vm.guardar();
    http.expectOne(URL + 'respuestas/').flush(detalle());
  });

  it('muestra obligatorias indicadas por el servidor ante cambios de contenido', async () => {
    http.expectOne(URL).flush(respondido());
    fixture.componentInstance.vm.finalizar();
    http
      .expectOne(URL + 'finalizar/')
      .flush(
        { detail: 'Faltan respuestas.', preguntas_pendientes: [detalle().preguntas[0].id] },
        { status: 400, statusText: 'Bad Request' },
      );
    await fixture.whenStable();
    expect(fixture.nativeElement.querySelectorAll('.missing')).toHaveLength(1);
    expect(navigate).not.toHaveBeenCalled();
  });

  it('volver al dashboard guarda los cambios antes de navegar', () => {
    http.expectOne(URL).flush(detalle());
    const vm = fixture.componentInstance.vm;
    vm.set(detalle().preguntas[1].id, 'Guardar antes de volver');
    vm.volver();
    expect(navigate).not.toHaveBeenCalled();
    http.expectOne(URL + 'respuestas/').flush(detalle());
    expect(navigate).toHaveBeenCalledWith('/dashboard/nuevo-trabajador');
  });

  it('el acceso directo a una pendiente permite comenzar solo si está configurada', async () => {
    const data = {
      ...detalle(),
      estado_asignacion: 'PENDIENTE',
      estado_aplicacion: null,
      aplicacion_id: null,
    };
    http.expectOne(URL).flush(data);
    fixture.componentInstance.vm.iniciar();
    http.expectOne(URL + 'iniciar/').flush(detalle());
    await fixture.whenStable();
    expect(fixture.componentInstance.vm.editable()).toBe(true);
  });

  it('sin configuración no permite comenzar desde enlace directo', async () => {
    http.expectOne(URL).flush({
      ...detalle(),
      disponible: false,
      preguntas: [],
      estado_asignacion: 'PENDIENTE',
      aplicacion_id: null,
      estado_aplicacion: null,
    });
    fixture.componentInstance.vm.iniciar();
    await fixture.whenStable();
    expect(fixture.nativeElement.textContent).toContain(
      'La evaluación inicial todavía está siendo configurada.',
    );
    http.expectNone(URL + 'iniciar/');
  });
});

describe('Navegación dashboard y evaluación', () => {
  let http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter(routes),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: '/api' },
        {
          provide: AuthService,
          useValue: {
            user: signal(user),
            restoreSession() {
              return of(this.user());
            },
            refreshIdentity() {
              this.user.set(worker);
              return of(worker);
            },
            logout: vi.fn(),
          },
        },
      ],
    });
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => {
    http.verify();
    vi.restoreAllMocks();
  });

  it('comienza desde dashboard y abre el formulario después de crear la aplicación', async () => {
    const harness = await RouterTestingHarness.create();
    const dashboard = await harness.navigateByUrl(user.dashboard_path, NuevoTrabajadorDashboard);
    http.expectOne('/api/nuevo-trabajador/dashboard/').flush(resumen('PENDIENTE'));
    dashboard.vm.comenzar();
    const request = http.expectOne(URL + 'iniciar/');
    expect(request.request.body).toEqual({});
    request.flush(detalle());
    await harness.fixture.whenStable();
    expect(TestBed.inject(Router).url).toBe(PATH);
    http.expectOne(URL).flush(detalle());
  });

  it('continuar consulta respuestas existentes sin volver a iniciar', async () => {
    const harness = await RouterTestingHarness.create();
    const dashboard = await harness.navigateByUrl(user.dashboard_path, NuevoTrabajadorDashboard);
    http.expectOne('/api/nuevo-trabajador/dashboard/').flush(resumen('EN_PROGRESO'));
    dashboard.vm.continuar();
    await harness.fixture.whenStable();
    http.expectOne(URL).flush(respondido());
    http.expectNone(URL + 'iniciar/');
    expect(TestBed.inject(Router).url).toBe(PATH);
  });

  it('finalizar muestra éxito y continuar navega al trabajador; no vuelve al panel de nuevo trabajador', async () => {
    const harness = await RouterTestingHarness.create();
    const component = await harness.navigateByUrl(PATH, EvaluacionInicialComponent);
    http.expectOne(URL).flush(respondido());
    component.vm.finalizar();
    http.expectOne(URL + 'finalizar/').flush(resultado());
    await harness.fixture.whenStable();
    expect(TestBed.inject(Router).url).toBe(PATH);
    expect(harness.routeNativeElement?.textContent).toContain('Evaluación inicial completada');
    component.vm.continuar();
    await harness.fixture.whenStable();
    expect(TestBed.inject(Router).url).toBe(worker.dashboard_path);
    await harness.navigateByUrl(user.dashboard_path);
    expect(TestBed.inject(Router).url).toBe(worker.dashboard_path);
    await harness.navigateByUrl(PATH);
    expect(TestBed.inject(Router).url).toBe(worker.dashboard_path);
    http.expectNone('/api/nuevo-trabajador/dashboard/');
  });

  it('conserva los tres guards en la ruta nueva', () => {
    const parent = routes.find((r) => r.path === 'dashboard')!;
    expect(parent.canActivate).toContain(authGuard);
    expect(parent.canActivateChild).toContain(primerAccesoGuard);
    const child = parent.children!.find(
      (r) => r.path === 'nuevo-trabajador/evaluacion/:asignacionId',
    )!;
    expect(child.canActivate).toContain(roleGuard);
    expect(child.data?.['role']).toBe('NUEVO_TRABAJADOR');
  });
});
