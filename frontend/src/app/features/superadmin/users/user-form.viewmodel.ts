/**
 * Prepara alta o edición con SuperadminService, catálogos activos y datos de la persona cuando
 * hay ID. Gestiona validación, confirmación visual de alta SUPERADMIN y navegación al detalle;
 * el backend vuelve a validar las reglas.
 */
import { DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { finalize, forkJoin } from 'rxjs';
import { CREATION_ROLES, Institution, Person } from '../superadmin.models';
import { apiError, SuperadminService } from '../superadmin.service';
import { passwordsMatch, passwordStrength } from './password-validation';

@Injectable()
export class UserFormViewModel {
  private readonly api = inject(SuperadminService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  readonly id = Number(inject(ActivatedRoute).snapshot.paramMap.get('id')) || null;
  readonly roles = CREATION_ROLES;
  readonly person = signal<Person | null>(null);
  readonly areas = signal<Institution[]>([]);
  readonly cargos = signal<Institution[]>([]);
  readonly loading = signal(true);
  readonly ready = signal(false);
  readonly saving = signal(false);
  readonly error = signal('');
  readonly showPassword = signal(false);
  readonly confirmSuperadmin = signal(false);
  readonly form = inject(FormBuilder).nonNullable.group(
    {
      email: ['', [Validators.required, Validators.email, Validators.maxLength(150)]],
      password: ['', [Validators.required, passwordStrength, Validators.maxLength(128)]],
      password_confirmation: ['', Validators.required],
      role: ['NUEVO_TRABAJADOR', Validators.required],
      codigo_empleado: ['', [Validators.required, Validators.maxLength(50)]],
      first_name: ['', [Validators.required, Validators.maxLength(150)]],
      last_name: ['', [Validators.required, Validators.maxLength(150)]],
      apellido_materno: ['', Validators.maxLength(150)],
      nombre_preferido: ['', Validators.maxLength(150)],
      fecha_nacimiento: '',
      sexo: '',
      telefono: ['', Validators.maxLength(30)],
      area_id: [null as number | null],
      cargo_id: [null as number | null],
      habilitado_asignaciones: true,
    },
    { validators: passwordsMatch },
  );

  /**
   * En edición retira validadores de clave porque se cambia desde otra pantalla; inicia carga
   * de catálogos y persona.
   */
  constructor() {
    if (this.id) {
      this.form.controls.password.clearValidators();
      this.form.controls.password_confirmation.clearValidators();
      this.form.controls.password.updateValueAndValidity();
      this.form.controls.password_confirmation.updateValueAndValidity();
    }
    this.load();
  }
  /**
   * Carga áreas/cargos activos y luego la ficha si existe ID. Conserva IDs históricos
   * inactivos sin reemplazarlos y habilita ready solo al completar datos; fallos se muestran
   * para reintentar.
   */
  load() {
    this.loading.set(true);
    this.error.set('');
    this.ready.set(false);
    forkJoin({
      areas: this.api.institution('areas', true),
      cargos: this.api.institution('cargos', true),
    })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (data) => {
          this.areas.set(data.areas);
          this.cargos.set(data.cargos);
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
                  this.form.patchValue({
                    ...person,
                    role: person.role || '',
                    fecha_nacimiento: person.fecha_nacimiento || '',
                    area_id: person.area?.id ?? null,
                    cargo_id: person.cargo?.id ?? null,
                  });
                  // Un vínculo histórico inactivo se conserva hasta que la persona elija reemplazarlo.
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
  invalid(name: string) {
    const field = this.form.get(name);
    return !!field?.touched && field.invalid;
  }
  /**
   * Valida preparación y formulario, exige confirmación visual al crear SUPERADMIN y construye
   * payload. En edición omite rol/contraseña; solo psicólogos envían habilitado_asignaciones.
   * Al guardar vacía claves y navega al detalle con aviso; errores quedan en pantalla.
   */
  submit() {
    if (this.saving() || !this.ready()) return;
    this.form.markAllAsTouched();
    this.error.set('');
    if (this.form.invalid) {
      this.error.set('Revisa los campos obligatorios y las contraseñas.');
      return;
    }
    const value = this.form.getRawValue();
    if (!this.id && value.role === 'SUPERADMIN' && !this.confirmSuperadmin()) {
      this.error.set('Confirma la administración global antes de crear otro Superadmin.');
      return;
    }
    const { password, password_confirmation, role, habilitado_asignaciones, ...personal } = value;
    const data = {
      ...personal,
      email: personal.email.trim().toLowerCase(),
      fecha_nacimiento: personal.fecha_nacimiento || null,
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
        next: (person) => {
          this.form.controls.password.reset();
          this.form.controls.password_confirmation.reset();
          void this.router.navigate(['/dashboard/superadmin/personas', person.id], {
            queryParams: { saved: this.id ? 'updated' : 'created' },
          });
        },
        error: (e) => this.error.set(apiError(e)),
      });
  }
}
