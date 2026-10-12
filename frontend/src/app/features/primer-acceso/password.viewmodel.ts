import { HttpErrorResponse } from '@angular/common/http';
import { DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs';
import { AuthService } from '../../core/auth/auth.service';
import { passwordsMatch, passwordStrength } from '../superadmin/users/password-validation';
import { PrimerAccesoService } from './primer-acceso.service';

@Injectable()
export class PrimerAccesoPasswordViewModel {
  private readonly api = inject(PrimerAccesoService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  readonly auth = inject(AuthService);
  readonly saving = signal(false);
  readonly error = signal('');
  readonly form = inject(FormBuilder).nonNullable.group(
    {
      password: ['', [Validators.required, Validators.maxLength(128), passwordStrength]],
      password_confirmation: ['', [Validators.required, Validators.maxLength(128)]],
    },
    { validators: passwordsMatch },
  );

  fieldError(name: 'password' | 'password_confirmation'): string {
    const control = this.form.controls[name];
    if (!control.touched) return '';
    if (control.hasError('server')) return control.getError('server');
    if (control.hasError('required')) return 'Este campo es obligatorio.';
    if (control.hasError('maxlength')) return 'Máximo 128 caracteres.';
    if (control.hasError('passwordStrength'))
      return 'Usa al menos 8 caracteres, una letra y un número.';
    if (name === 'password_confirmation' && this.form.hasError('passwordsMatch'))
      return 'Las contraseñas no coinciden.';
    return '';
  }

  submit() {
    if (this.saving()) return;
    this.form.markAllAsTouched();
    this.error.set('');
    if (this.form.invalid) return;
    this.saving.set(true);
    this.api
      .cambiarPassword(this.form.getRawValue())
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.saving.set(false)),
      )
      .subscribe({
        next: (estado) => {
          this.form.reset();
          void this.router.navigateByUrl(estado.siguiente_ruta);
        },
        error: (error: HttpErrorResponse) => {
          for (const field of ['password', 'password_confirmation'] as const) {
            const messages = error.error?.[field];
            if (messages)
              this.form.controls[field].setErrors({
                server: Array.isArray(messages) ? messages.join(' ') : String(messages),
              });
          }
          this.error.set(
            error.error?.detail || 'No se pudo guardar. Revisa los campos e inténtalo de nuevo.',
          );
        },
      });
  }
}
