import { computed, DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs';
import { Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { EvaluacionService } from './evaluacion.service';
import { AuthService } from '../../core/auth/auth.service';
import { EvaluacionInicial } from './dashboard.models';
import { NuevoTrabajadorService } from './dashboard.service';

@Injectable()
export class NuevoTrabajadorDashboardViewModel {
  private readonly auth = inject(AuthService);
  private readonly api = inject(NuevoTrabajadorService);
  private readonly evaluacionApi = inject(EvaluacionService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  readonly user = this.auth.user;
  readonly nombreCompleto = computed(() =>
    [this.user()?.first_name, this.user()?.last_name].filter(Boolean).join(' ').trim(),
  );
  readonly primerNombre = computed(() => this.user()?.first_name.trim().split(/\s+/)[0] ?? '');
  readonly evaluacion = signal<EvaluacionInicial | null>(null);
  readonly loading = signal(false);
  readonly error = signal('');
  readonly starting = signal(false);
  readonly startError = signal('');

  constructor() {
    this.load();
  }

  load(): void {
    if (this.loading()) return;
    this.loading.set(true);
    this.error.set('');
    this.evaluacion.set(null);
    this.api
      .resumen()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (resumen) => this.evaluacion.set(resumen.evaluacion_inicial),
        error: () =>
          this.error.set('No pudimos consultar tu evaluación inicial. Intenta nuevamente.'),
      });
  }

  logout(): void {
    this.auth.logout();
  }

  comenzar(): void {
    const evaluacion = this.evaluacion();
    if (!evaluacion?.puede_iniciar || !evaluacion.asignacion_id || this.starting()) return;
    this.starting.set(true);
    this.startError.set('');
    this.evaluacionApi
      .iniciar(evaluacion.asignacion_id)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.starting.set(false)),
      )
      .subscribe({
        next: () => this.abrir(evaluacion.asignacion_id!),
        error: (error: HttpErrorResponse) =>
          this.startError.set(
            typeof error.error?.detail === 'string'
              ? error.error.detail
              : 'No se pudo iniciar la evaluación. Intenta nuevamente.',
          ),
      });
  }

  continuar(): void {
    const evaluacion = this.evaluacion();
    if (evaluacion?.estado === 'EN_PROGRESO' && evaluacion.asignacion_id)
      this.abrir(evaluacion.asignacion_id);
  }

  private abrir(id: string): void {
    void this.router.navigateByUrl(`/dashboard/nuevo-trabajador/evaluacion/${id}`);
  }
}
