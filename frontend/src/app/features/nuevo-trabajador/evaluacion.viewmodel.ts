import { HttpErrorResponse } from '@angular/common/http';
import { computed, DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { finalize, switchMap, tap } from 'rxjs';
import { AuthService } from '../../core/auth/auth.service';
import {
  EvaluacionDetalle,
  PreguntaEvaluacion,
  RespuestaEvaluacion,
  ValorRespuesta,
  ResultadoEvaluacion,
} from './evaluacion.models';
import { EvaluacionService } from './evaluacion.service';

@Injectable()
export class EvaluacionViewModel {
  private readonly api = inject(EvaluacionService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  readonly id = inject(ActivatedRoute).snapshot.paramMap.get('asignacionId')!;
  readonly detalle = signal<EvaluacionDetalle | null>(null);
  readonly resultado = signal<ResultadoEvaluacion | null>(null);
  readonly identidadLista = signal(false);
  readonly valores = signal<Record<string, ValorRespuesta>>({});
  readonly loading = signal(false);
  readonly operacion = signal<'iniciando' | 'guardando' | 'finalizando' | 'identidad' | null>(null);
  readonly saving = computed(() => this.operacion() !== null);
  readonly bloqueado = computed(() => this.loading() || this.saving());
  readonly sesionInvalida = signal(false);
  readonly dirty = signal(false);
  readonly error = signal('');
  readonly mensaje = signal('');
  readonly pendientes = signal<string[]>([]);
  readonly focoPendiente = signal<{ id: string } | null>(null);
  readonly estado = computed(() =>
    this.resultado() ? 'COMPLETADA' : this.detalle()?.estado_asignacion,
  );
  readonly completada = computed(() => this.estado() === 'COMPLETADA');
  readonly total = computed(() => this.detalle()?.preguntas.length ?? 0);
  readonly configurada = computed(() => !!this.detalle()?.disponible && this.total() > 0);
  readonly puedeIniciar = computed(
    () => this.estado() === 'PENDIENTE' && this.configurada() && !this.sesionInvalida(),
  );
  readonly seguimiento = computed(() =>
    this.resultado()?.estado_asignacion_profesional === 'ASIGNADO'
      ? 'Profesional asignado'
      : 'Asignación profesional pendiente',
  );
  readonly procesando = computed(() => {
    switch (this.operacion()) {
      case 'iniciando':
        return 'Iniciando evaluación…';
      case 'guardando':
        return 'Guardando progreso…';
      case 'finalizando':
        return 'Finalizando evaluación…';
      case 'identidad':
        return 'Actualizando tu sesión…';
      default:
        return '';
    }
  });
  readonly editable = computed(
    () =>
      !this.resultado() &&
      !this.sesionInvalida() &&
      this.detalle()?.estado_aplicacion === 'INICIADA' &&
      this.detalle()?.estado_asignacion === 'EN_PROGRESO' &&
      this.configurada(),
  );
  readonly respondidas = computed(
    () => this.detalle()?.preguntas.filter((p) => this.respondida(p)).length ?? 0,
  );
  readonly porcentaje = computed(() => {
    const total = this.total();
    return total ? Math.round((this.respondidas() * 100) / total) : 0;
  });

  constructor() {
    this.load();
  }

  load(): void {
    if (this.bloqueado() || this.dirty() || this.resultado() || this.sesionInvalida()) return;
    this.loading.set(true);
    this.error.set('');
    this.api
      .consultar(this.id)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (data) => this.hydrate(data),
        error: (error) => this.fail(error),
      });
  }

  private hydrate(data: EvaluacionDetalle): void {
    this.detalle.set({ ...data, preguntas: [...data.preguntas].sort((a, b) => a.orden - b.orden) });
    this.valores.set(
      Object.fromEntries(
        data.respuestas.map((r) => [
          r.pregunta_id,
          r.opcion_id ?? r.valor_texto ?? r.valor_numerico ?? r.valor_booleano ?? null,
        ]),
      ),
    );
    this.dirty.set(false);
    this.pendientes.set([]);
  }

  set(id: string, value: ValorRespuesta): void {
    if (!this.editable() || this.bloqueado()) return;
    this.valores.update((values) => ({ ...values, [id]: value }));
    this.dirty.set(true);
    this.mensaje.set('');
    this.pendientes.update((ids) => ids.filter((pk) => pk !== id));
  }

  private respondida(p: PreguntaEvaluacion): boolean {
    const value = this.valores()[p.id];
    if (value === undefined || value === null || (typeof value === 'string' && !value.trim()))
      return false;
    if (p.tipo_respuesta === 'ESCALA') return p.opciones.some((o) => o.id === value);
    if (p.tipo_respuesta === 'BOOLEANO') return typeof value === 'boolean';
    if (p.tipo_respuesta === 'NUMERO')
      return typeof value === 'string' && Number.isFinite(Number(value));
    return typeof value === 'string';
  }

  private answers(): RespuestaEvaluacion[] {
    return (this.detalle()?.preguntas ?? []).map((p) => {
      const value = this.valores()[p.id] ?? null;
      return {
        pregunta_id: p.id,
        opcion_id: p.tipo_respuesta === 'ESCALA' ? (value as string | null) : null,
        valor_texto: p.tipo_respuesta === 'TEXTO' ? (value as string | null)?.trim() || null : null,
        valor_numerico: p.tipo_respuesta === 'NUMERO' ? (value as string | null) : null,
        valor_booleano: p.tipo_respuesta === 'BOOLEANO' ? (value as boolean | null) : null,
      };
    });
  }

  iniciar(): void {
    if (this.bloqueado() || !this.puedeIniciar()) return;
    this.operacion.set('iniciando');
    this.error.set('');
    this.api
      .iniciar(this.id)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.operacion.set(null)),
      )
      .subscribe({
        next: (data) => this.hydrate(data),
        error: (error) => this.fail(error),
      });
  }

  guardar(volver = false): void {
    if (!this.editable() || this.bloqueado()) return;
    this.operacion.set('guardando');
    this.error.set('');
    this.mensaje.set('');
    this.api
      .guardar(this.id, this.answers())
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.operacion.set(null)),
      )
      .subscribe({
        next: (data) => {
          this.hydrate(data);
          this.mensaje.set('Progreso guardado. Puedes continuar más adelante.');
          if (volver) void this.router.navigateByUrl('/dashboard/nuevo-trabajador');
        },
        error: (error) => this.fail(error),
      });
  }

  finalizar(): void {
    if (!this.editable() || this.bloqueado()) return;
    const missing = this.detalle()!
      .preguntas.filter((p) => p.obligatoria && !this.respondida(p))
      .map((p) => p.id);
    this.pendientes.set(missing);
    this.error.set('');
    this.mensaje.set('');
    if (missing.length) {
      this.error.set('Responde las preguntas obligatorias indicadas antes de finalizar.');
      this.focoPendiente.set({ id: missing[0] });
      return;
    }
    this.operacion.set('finalizando');
    this.api
      .finalizar(this.id, this.answers())
      .pipe(
        tap((data) => {
          this.resultado.set(data);
          this.dirty.set(false);
          this.operacion.set('identidad');
        }),
        switchMap(() => this.auth.refreshIdentity()),
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.operacion.set(null)),
      )
      .subscribe({
        next: (user) => {
          this.identidadLista.set(user?.role === 'TRABAJADOR');
          if (!this.identidadLista())
            this.error.set('No se pudo actualizar tu sesión. Intenta continuar nuevamente.');
        },
        error: (error) => this.fail(error),
      });
  }

  volver(): void {
    if (this.bloqueado()) return;
    if (this.resultado()) {
      this.continuar();
      return;
    }
    if (this.dirty() && this.editable()) this.guardar(true);
    else void this.router.navigateByUrl('/dashboard/nuevo-trabajador');
  }

  continuar(): void {
    if (!this.resultado() || this.bloqueado() || this.sesionInvalida()) return;
    if (this.identidadLista() && this.auth.user()?.role === 'TRABAJADOR') {
      void this.router.navigateByUrl(this.auth.user()!.dashboard_path);
      return;
    }
    this.operacion.set('identidad');
    this.error.set('');
    this.auth
      .refreshIdentity()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.operacion.set(null)),
      )
      .subscribe({
        next: (user) => {
          this.identidadLista.set(user?.role === 'TRABAJADOR');
          if (this.identidadLista()) void this.router.navigateByUrl(user!.dashboard_path);
          else this.error.set('No se pudo actualizar tu sesión. Intenta continuar nuevamente.');
        },
        error: (error) => this.fail(error),
      });
  }

  private fail(error: HttpErrorResponse): void {
    this.sesionInvalida.set(error.status === 401);
    this.error.set(
      error.status === 401
        ? 'Tu sesión ya no es válida. Vuelve a iniciar sesión.'
        : error.status === 403
          ? 'No tienes acceso a esta evaluación. Vuelve a tu panel.'
          : error.status === 404
            ? 'Esta evaluación no está disponible. Vuelve a tu panel.'
            : error.status === 400 && typeof error.error?.detail === 'string'
              ? error.error.detail
              : this.resultado()
                ? 'Tu evaluación está completada. No pudimos actualizar tu sesión; pulsa Continuar a mi panel para reintentar.'
                : !this.detalle()
                  ? 'No pudimos cargar la evaluación. Intenta nuevamente.'
                  : this.operacion() === 'iniciando'
                    ? 'No se pudo iniciar la evaluación. Intenta nuevamente.'
                    : 'No pudimos completar la solicitud. Tus cambios siguen en esta pantalla; intenta nuevamente.',
    );
    this.pendientes.set(
      Array.isArray(error.error?.preguntas_pendientes)
        ? (this.detalle()
            ?.preguntas.filter((p) => error.error.preguntas_pendientes.includes(p.id))
            .map((p) => p.id) ?? [])
        : [],
    );
    if (this.pendientes().length) this.focoPendiente.set({ id: this.pendientes()[0] });
  }

  iniciarSesion(): void {
    this.auth.logout();
  }
}
