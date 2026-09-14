/**
 * Pantalla y ViewModel de restablecimiento administrativo. Carga la persona por ID, valida
 * clave/confirmación y llama SuperadminService.password; tras éxito vacía y oculta ambos
 * campos. No es un flujo de recuperación pública por correo.
 */
import { Component, DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { Person } from '../superadmin.models';
import { apiError, SuperadminService } from '../superadmin.service';
import { passwordsMatch, passwordStrength } from './password-validation';

@Injectable()
/**
 * Carga la persona objetivo y administra clave, confirmación, estado de envío y mensajes.
 */
export class UserPasswordViewModel {
  private readonly api = inject(SuperadminService);
  private readonly destroyRef = inject(DestroyRef);
  readonly id = Number(inject(ActivatedRoute).snapshot.paramMap.get('id'));
  readonly person = signal<Person | null>(null);
  readonly error = signal('');
  readonly notice = signal('');
  readonly busy = signal(false);
  readonly showPassword = signal(false);
  readonly form = inject(FormBuilder).nonNullable.group(
    {
      password: ['', [Validators.required, passwordStrength, Validators.maxLength(128)]],
      password_confirmation: ['', Validators.required],
    },
    { validators: passwordsMatch },
  );
  constructor() {
    this.api
      .user(this.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({ next: (p) => this.person.set(p), error: (e) => this.error.set(apiError(e)) });
  }
  /**
   * Exige persona cargada y formulario válido; solicita reset-password. Al éxito borra valores
   * y oculta claves; errores se muestran con apiError y busy impide doble envío.
   */
  submit() {
    if (this.busy() || !this.person()) return;
    this.form.markAllAsTouched();
    this.error.set('');
    this.notice.set('');
    if (this.form.invalid) return;
    this.busy.set(true);
    this.api
      .password(this.id, this.form.getRawValue())
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.busy.set(false)),
      )
      .subscribe({
        next: () => {
          this.form.reset();
          this.showPassword.set(false);
          this.notice.set('Contraseña restablecida correctamente.');
        },
        error: (e) => this.error.set(apiError(e)),
      });
  }
}

@Component({
  selector: 'app-user-password',
  imports: [ReactiveFormsModule, RouterLink],
  providers: [UserPasswordViewModel],
  template: `
    <p class="eyebrow">SUPERADMIN / PERSONAS</p>
    <h1>Restablecer contraseña</h1>
    <p>{{ vm.person()?.email }}</p>
    @if (vm.error()) {
      <p class="sa-error" role="alert">{{ vm.error() }}</p>
    }
    @if (vm.notice()) {
      <p class="sa-success" role="status">{{ vm.notice() }}</p>
    }
    <form [formGroup]="vm.form" (ngSubmit)="vm.submit()" class="sa-panel sa-password">
      <label
        >Nueva contraseña<input
          [type]="vm.showPassword() ? 'text' : 'password'"
          formControlName="password"
          autocomplete="new-password"
          maxlength="128"
      /></label>
      <p class="sa-help">Mínimo 8 caracteres, una letra y un número.</p>
      @if (vm.form.controls.password.touched && vm.form.controls.password.invalid) {
        <p class="sa-field-error">La contraseña no cumple los requisitos.</p>
      }
      <label
        >Confirmar contraseña<input
          [type]="vm.showPassword() ? 'text' : 'password'"
          formControlName="password_confirmation"
          autocomplete="new-password"
          maxlength="128"
      /></label>
      @if (vm.form.controls.password_confirmation.touched && vm.form.hasError('passwordsMatch')) {
        <p class="sa-field-error">Las contraseñas no coinciden.</p>
      }
      <button class="sa-plain" type="button" (click)="vm.showPassword.set(!vm.showPassword())">
        {{ vm.showPassword() ? 'Ocultar contraseñas' : 'Mostrar contraseñas' }}
      </button>
      <div class="sa-actions">
        <button class="button" type="submit" [disabled]="vm.busy() || !vm.person()">
          {{ vm.busy() ? 'Guardando…' : 'Restablecer contraseña' }}</button
        ><a class="text-link" [routerLink]="['/dashboard/superadmin/personas', vm.id]"
          >Volver al detalle</a
        >
      </div>
    </form>
  `,
})
/**
 * Presenta el restablecimiento y enlace de vuelta a la ficha; la operación se coordina en el
 * ViewModel.
 */
export class UserPassword {
  readonly vm = inject(UserPasswordViewModel);
}
