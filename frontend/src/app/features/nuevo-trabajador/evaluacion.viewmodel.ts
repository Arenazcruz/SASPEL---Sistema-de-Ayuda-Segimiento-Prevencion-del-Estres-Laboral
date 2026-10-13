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
  readonly saving = signal(false);
  readonly dirty = signal(false);
  readonly error = signal('');
  readonly mensaje = signal('');
  readonly pendientes = signal<string[]>([]);
  readonly editable = computed(
    () =>
      !this.resultado() &&
      this.detalle()?.estado_aplicacion === 'INICIADA' &&
      this.detalle()?.estado_asignacion === 'EN_PROGRESO' &&
      this.detalle()?.disponible,
  );
  readonly respondidas = computed(
    () => this.detalle()?.preguntas.filter((p) => this.respondida(p)).length ?? 0,
  );
  readonly porcentaje = computed(() => {
    const total = this.detalle()?.preguntas.length ?? 0;
    return total ? Math.round((this.respondidas() * 100) / total) : 0;
  });

  constructor() {
    this.load();
  }

  load(): void {
    if (this.loading() || this.saving()) return;
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
    this.detalle.set(data);
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
    if (!this.editable() || this.saving()) return;
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
    if (
      this.saving() ||
      !this.detalle()?.disponible ||
      this.detalle()?.estado_asignacion !== 'PENDIENTE'
    )
      return;
    this.saving.set(true);
    this.error.set('');
    this.api
      .iniciar(this.id)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.saving.set(false)),
      )
      .subscribe({
        next: (data) => this.hydrate(data),
        error: (error) => this.fail(error),
      });
  }

  guardar(volver = false): void {
    if (!this.editable() || this.saving()) return;
    this.saving.set(true);
    this.error.set('');
    this.mensaje.set('');
    this.api
      .guardar(this.id, this.answers())
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.saving.set(false)),
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
    if (!this.editable() || this.saving()) return;
    const missing = this.detalle()!
      .preguntas.filter((p) => p.obligatoria && !this.respondida(p))
      .map((p) => p.id);
    this.pendientes.set(missing);
    this.error.set('');
    this.mensaje.set('');
    if (missing.length) {
      this.error.set('Responde las preguntas obligatorias indicadas antes de finalizar.');
      return;
    }
    this.saving.set(true);
    this.api
      .finalizar(this.id, this.answers())
      .pipe(
        tap((data) => {
          this.resultado.set(data);
          this.dirty.set(false);
        }),
        switchMap(() => this.auth.refreshIdentity()),
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.saving.set(false)),
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
    if (this.saving()) return;
    if (this.resultado()) {
      this.continuar();
      return;
    }
    if (this.dirty() && this.editable()) this.guardar(true);
    else void this.router.navigateByUrl('/dashboard/nuevo-trabajador');
  }

  continuar(): void {
    if (!this.resultado() || this.saving()) return;
    if (this.identidadLista()) {
      void this.router.navigateByUrl(this.auth.user()!.dashboard_path);
      return;
    }
    this.saving.set(true);
    this.error.set('');
    this.auth
      .refreshIdentity()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.saving.set(false)),
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
    this.error.set(
      typeof error.error?.detail === 'string'
        ? error.error.detail
        : 'No pudimos completar la solicitud. Tus cambios siguen en esta pantalla; intenta nuevamente.',
    );
    this.pendientes.set(
      Array.isArray(error.error?.preguntas_pendientes) ? error.error.preguntas_pendientes : [],
    );
  }
}
