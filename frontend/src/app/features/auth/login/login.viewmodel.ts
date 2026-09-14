/**
 * Estado del formulario de login: campos, carga, visibilidad de clave y errores HTTP. Usa
 * AuthService y Router; la vista solo enlaza este estado y llama submit.
 */
import { HttpErrorResponse } from '@angular/common/http';
import { DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs';
import { AuthService } from '../../../core/auth/auth.service';

@Injectable()
export class LoginViewModel {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  readonly form = inject(FormBuilder).nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
  });
  readonly loading = signal(false);
  readonly error = signal('');
  readonly showPassword = signal(false);

  /**
   * Valida el formulario y bloquea envíos repetidos; suscribe login con correo sin espacios y
   * clave intacta. Al éxito borra clave y navega al panel; al fallo presenta mensajes por
   * estado HTTP. Actualiza loading y cancela suscripción al destruir la vista.
   */
  submit(): void {
    if (this.loading()) return;
    this.form.markAllAsTouched();
    this.error.set('');
    if (this.form.invalid) return;
    this.loading.set(true);
    const { email, password } = this.form.getRawValue();
    this.auth
      .login(email.trim(), password)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (user) => {
          this.form.controls.password.reset();
          void this.router.navigateByUrl(user.dashboard_path);
        },
        error: (error: HttpErrorResponse) => {
          if (error.status === 403)
            this.error.set(error.error?.detail ?? 'Tu cuenta no está habilitada para ingresar.');
          else if (error.status === 0)
            this.error.set('No pudimos conectar con SASPEL. Inténtalo nuevamente.');
          else if (error.status === 401) this.error.set('Correo o contraseña incorrectos.');
          else
            this.error.set('No pudimos iniciar sesión. Revisa tus datos e inténtalo nuevamente.');
        },
      });
  }
}
