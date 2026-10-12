import { computed, DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs';
import { AuthService } from '../../core/auth/auth.service';
import { EvaluacionInicial } from './dashboard.models';
import { NuevoTrabajadorService } from './dashboard.service';

@Injectable()
export class NuevoTrabajadorDashboardViewModel {
  private readonly auth = inject(AuthService);
  private readonly api = inject(NuevoTrabajadorService);
  private readonly destroyRef = inject(DestroyRef);
  readonly user = this.auth.user;
  readonly nombreCompleto = computed(() =>
    [this.user()?.first_name, this.user()?.last_name].filter(Boolean).join(' ').trim(),
  );
  readonly primerNombre = computed(() => this.user()?.first_name.trim().split(/\s+/)[0] ?? '');
  readonly evaluacion = signal<EvaluacionInicial | null>(null);
  readonly loading = signal(false);
  readonly error = signal('');

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
}
