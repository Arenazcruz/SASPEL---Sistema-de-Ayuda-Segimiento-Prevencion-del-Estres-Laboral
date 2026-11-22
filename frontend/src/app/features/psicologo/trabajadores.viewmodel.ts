import { HttpErrorResponse } from '@angular/common/http';
import { computed, DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs';
import { AuthService } from '../../core/auth/auth.service';
import { MisTrabajadores } from './psicologo.models';
import { PsicologoService } from './psicologo.service';

@Injectable()
export class MisTrabajadoresViewModel {
  private readonly api = inject(PsicologoService);
  private readonly auth = inject(AuthService);
  private readonly destroyRef = inject(DestroyRef);
  readonly user = this.auth.user;
  readonly nombre = computed(
    () =>
      [this.user()?.first_name, this.user()?.last_name].filter(Boolean).join(' ') ||
      this.user()?.email,
  );
  readonly datos = signal<MisTrabajadores | null>(null);
  readonly loading = signal(false);
  readonly error = signal('');

  constructor() {
    this.load();
  }

  load(): void {
    if (this.loading()) return;
    this.loading.set(true);
    this.error.set('');
    this.datos.set(null);
    this.api
      .trabajadores()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (data) => this.datos.set(data),
        error: (error: HttpErrorResponse) =>
          this.error.set(
            error.status === 401
              ? 'Tu sesión ya no es válida. Vuelve a iniciar sesión.'
              : error.status === 403
                ? 'No tienes acceso a esta información.'
                : 'No pudimos consultar tus trabajadores. Intenta nuevamente.',
          ),
      });
  }

  logout(): void {
    this.auth.logout();
  }
}
