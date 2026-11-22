/**
 * Prepara alta o edición con SuperadminService, catálogos activos y datos de la persona cuando
 * hay ID. Gestiona validación, confirmación visual de alta SUPERADMIN y retorno al listado;
 * el backend vuelve a validar las reglas.
 */
import { DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { catchError, distinctUntilChanged, finalize, map, of, Subject, switchMap } from 'rxjs';
import { CREATION_ROLES, Institution, Person } from '../superadmin.models';
import { apiError, validationErrorMessage, SuperadminService } from '../superadmin.service';
import { passwordsMatch, passwordStrength } from './password-validation';
import {
  birthDate,
  birthDateBounds,
  employeeCode,
  normalizeName,
  personName,
  phoneNumber,
} from './user-validation';

@Injectable()
export class UserFormViewModel {
  private readonly api = inject(SuperadminService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  readonly id = inject(ActivatedRoute).snapshot.paramMap.get('id');
  readonly roles = CREATION_ROLES;
  readonly person = signal<Person | null>(null);
  readonly areas = signal<Institution[]>([]);
  readonly cargos = signal<Institution[]>([]);
  readonly cargosLoading = signal(false);
  readonly cargosError = signal('');
  readonly cargoNotice = signal('');
  private readonly cargoRequests = new Subject<{ area: string | null; current: string | null }>();
  private cargoToRestore: string | null = null;
  readonly loading = signal(true);
  readonly ready = signal(false);
  readonly saving = signal(false);
  readonly error = signal('');
  readonly showPassword = signal(false);
  readonly confirmSuperadmin = signal(false);
  readonly form = inject(FormBuilder).nonNullable.group(
    {
      password: ['', [Validators.required, passwordStrength, Validators.maxLength(128)]],
      password_confirmation: ['', Validators.required],
      role: ['NUEVO_TRABAJADOR', Validators.required],
      codigo_empleado: ['', [Validators.required, Validators.maxLength(50), employeeCode]],
      first_name: ['', [Validators.required, Validators.maxLength(150), personName]],
      last_name: ['', [Validators.required, Validators.maxLength(150), personName]],
      apellido_materno: ['', [Validators.maxLength(150), personName]],
      fecha_nacimiento: ['', [Validators.required, birthDate]],
      sexo: '',
      telefono: ['', [Validators.maxLength(15), phoneNumber]],
      area_id: [null as string | null],
      cargo_id: [null as string | null],
      habilitado_asignaciones: true,
    },
    { validators: passwordsMatch },
  );

  /**
   * En edición retira validadores de clave porque se cambia desde otra pantalla; inicia carga
   * de catálogos y persona.
   */
  constructor() {
    this.form.controls.cargo_id.disable({ emitEvent: false });
    this.cargoRequests
      .pipe(
        switchMap(({ area, current }) => {
          this.form.controls.cargo_id.reset(null, { emitEvent: false });
          this.form.controls.cargo_id.disable({ emitEvent: false });
          this.cargos.set([]);
          this.cargosError.set('');
          this.cargoNotice.set('');
          this.cargosLoading.set(!!area);
          if (!area) return of(null);
          return this.api.institution('cargos', true, area).pipe(
            map((cargos) => ({ cargos, current })),
            catchError((error) => {
              this.cargosError.set(apiError(error));
              return of(null);
            }),
            finalize(() => this.cargosLoading.set(false)),
          );
        }),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((result) => {
        if (!result) return;
        this.cargos.set(result.cargos);
        this.form.controls.cargo_id.enable({ emitEvent: false });
        if (result.current && result.cargos.some((cargo) => cargo.id === result.current)) {
          this.form.controls.cargo_id.setValue(result.current, { emitEvent: false });
        } else if (result.current) {
          this.cargoNotice.set(
            'El cargo anterior ya no está disponible para esta área. Selecciona otro cargo si corresponde.',
          );
        }
      });
    this.form.controls.area_id.valueChanges
      .pipe(distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe((area) => this.loadCargos(area));
    if (this.id) {
      this.form.controls.fecha_nacimiento.removeValidators(Validators.required);
      this.form.controls.fecha_nacimiento.updateValueAndValidity();
      this.form.controls.password.clearValidators();
      this.form.controls.password_confirmation.clearValidators();
      this.form.controls.password.updateValueAndValidity();
      this.form.controls.password_confirmation.updateValueAndValidity();
    }
    this.load();
  }
  /**
   * Carga áreas y la ficha si existe ID. Los cargos se consultan únicamente para el área
   * seleccionada; en edición conserva el cargo solo si sigue siendo una opción válida.
   */
  load() {
    this.loading.set(true);
    this.error.set('');
    this.ready.set(false);
    this.api
      .institution('areas', true)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (areas) => {
          this.areas.set(areas);
          if (this.id)
            this.api
              .user(this.id)
              .pipe(
                takeUntilDestroyed(this.destroyRef),
                finalize(() => this.loading.set(false)),
              )
              .subscribe({
                next: (person) => {
                  this.person.set(person);
                  if (person.fecha_nacimiento) {
                    this.form.controls.fecha_nacimiento.addValidators(Validators.required);
                  }
                  this.form.patchValue(
                    {
                      ...person,
                      role: person.role || '',
                      fecha_nacimiento: person.fecha_nacimiento || '',
                      area_id: person.area?.id ?? null,
                      cargo_id: null,
                    },
                    { emitEvent: false },
                  );
                  this.loadCargos(person.area?.id ?? null, person.cargo?.id ?? null);
                  this.ready.set(true);
                },
                error: (e) => this.error.set(apiError(e)),
              });
          else {
            this.loading.set(false);
            this.ready.set(true);
          }
        },
        error: (e) => {
          this.loading.set(false);
          this.error.set(apiError(e));
        },
      });
  }
  loadCargos(area = this.form.controls.area_id.value, current: string | null = null) {
    this.cargoToRestore = current;
    this.cargoRequests.next({ area, current });
  }
  retryCargos() {
    this.loadCargos(this.form.controls.area_id.value, this.cargoToRestore);
  }
  invalid(name: string) {
    const field = this.form.get(name);
    return !!field?.touched && field.invalid;
  }
  birthDateLimits = birthDateBounds;
  fieldError(name: string): string {
    const errors = this.form.get(name)?.errors;
    if (!errors) return '';
    if (errors['server']) return errors['server'];
    if (errors['required']) return 'Este campo es obligatorio.';
    if (errors['maxlength']) return `Máximo ${errors['maxlength'].requiredLength} caracteres.`;
    if (errors['personName']) return 'Usa solo letras y espacios; se permiten tildes y ñ.';
    if (errors['employeeCode'])
      return 'Usa letras y números, con guiones entre grupos; sin espacios.';
    if (errors['phoneNumber'])
      return 'El teléfono debe contener entre 8 y 15 dígitos, sin letras ni símbolos.';
    if (errors['birthDate']) return 'Ingresa una fecha de nacimiento válida.';
    if (errors['ageRange'])
      return 'La edad debe ser mayor de 18 y menor de 78 años (19 a 77 años cumplidos).';
    return 'Revisa el valor de este campo.';
  }
  emailPreview() {
    if (this.id) return this.person()?.email || '';
    const part = (value: string) =>
      (value.trim().split(/\s+/)[0] || '')
        .normalize('NFKD')
        .replace(/[^\x00-\x7F]/g, '')
        .toLowerCase()
        .replace(/[^a-z0-9]/g, '');
    const first = part(this.form.controls.first_name.value);
    const last = part(this.form.controls.last_name.value);
    if (!first || !last) return '';
    let nameSize = Math.min(first.length, 31);
    const lastSize = Math.min(last.length, 63 - nameSize);
    nameSize = Math.min(first.length, 63 - lastSize);
    return `${first.slice(0, nameSize)}.${last.slice(0, lastSize)}@saspel.com`;
  }
  /**
   * Valida preparación y formulario, exige confirmación visual al crear SUPERADMIN y construye
   * payload. En edición omite rol/contraseña; solo psicólogos envían habilitado_asignaciones.
   * Al guardar vacía claves y vuelve al listado conservando filtros; errores quedan en el modal.
   */
  submit() {
    if (this.saving() || !this.ready() || this.cargosLoading() || this.cargosError()) return;
    const raw = this.form.getRawValue();
    this.form.patchValue({
      first_name: normalizeName(raw.first_name),
      last_name: normalizeName(raw.last_name),
      apellido_materno: normalizeName(raw.apellido_materno),
      codigo_empleado: raw.codigo_empleado.trim(),
      telefono: raw.telefono.trim(),
    });
    this.form.markAllAsTouched();
    this.error.set('');
    if (this.form.invalid) {
      this.error.set('Revisa los campos indicados antes de guardar.');
      return;
    }
    const value = this.form.getRawValue();
    if (!this.id && value.role === 'SUPERADMIN' && !this.confirmSuperadmin()) {
      this.error.set('Confirma la administración global antes de crear otro Superadmin.');
      return;
    }
    const {
      password,
      password_confirmation,
      role,
      habilitado_asignaciones,
      fecha_nacimiento,
      ...personal
    } = value;
    const data = {
      ...personal,
      ...(fecha_nacimiento ? { fecha_nacimiento } : {}),
      ...(role === 'PSICOLOGO' ? { habilitado_asignaciones } : {}),
      ...(!this.id ? { password, password_confirmation, role } : {}),
    };
    this.saving.set(true);
    (this.id ? this.api.update(this.id, data) : this.api.create(data))
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.saving.set(false)),
      )
      .subscribe({
        next: () => {
          this.form.controls.password.reset();
          this.form.controls.password_confirmation.reset();
          void this.router.navigate(['/dashboard/superadmin/personas'], {
            queryParamsHandling: 'preserve',
          });
        },
        error: (e) => {
          let fields = false;
          if (e.status === 400 && e.error && typeof e.error === 'object') {
            for (const [name, messages] of Object.entries(e.error)) {
              const control = this.form.get(name);
              if (!control) continue;
              const message = validationErrorMessage(messages);
              control.setErrors({ ...control.errors, server: message });
              control.markAsTouched();
              fields = true;
            }
          }
          this.error.set(fields ? 'Revisa los campos indicados antes de guardar.' : apiError(e));
        },
      });
  }
}
