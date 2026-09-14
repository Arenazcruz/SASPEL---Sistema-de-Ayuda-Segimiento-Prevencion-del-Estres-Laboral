/** Valida claves de alta/reset; sincronizar con superadmin.py y validadores Django. */
import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

/**
 * Devuelve error passwordStrength o null para un control: mínimo 8 caracteres, letra y número.
 * No reemplaza los validadores adicionales de Django.
 */
export const passwordStrength: ValidatorFn = (control: AbstractControl): ValidationErrors | null =>
  typeof control.value === 'string' &&
  control.value.length >= 8 &&
  /\p{L}/u.test(control.value) &&
  /\d/.test(control.value)
    ? null
    : { passwordStrength: true };

/**
 * Compara password/password_confirmation del grupo y devuelve error passwordsMatch o null sin
 * modificar campos.
 */
export const passwordsMatch: ValidatorFn = (control: AbstractControl): ValidationErrors | null =>
  control.get('password')?.value === control.get('password_confirmation')?.value
    ? null
    : { passwordsMatch: true };
