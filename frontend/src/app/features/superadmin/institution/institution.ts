/**
 * Pantalla compartida de áreas y cargos. InstitutionViewModel lee kind de la ruta, carga el
 * catálogo y gestiona alta, edición y activación con SuperadminService. Desactivar conserva
 * los vínculos de personas; la plantilla está en este archivo.
 */
import { Component, DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { finalize } from 'rxjs';
import { Institution, InstitutionKind } from '../superadmin.models';
import { apiError, SuperadminService } from '../superadmin.service';

@Injectable()
/**
 * Estado del catálogo elegido por data.kind; comparte formulario y acciones de áreas y cargos.
 */
export class InstitutionViewModel {
  private readonly api = inject(SuperadminService);
  private readonly destroyRef = inject(DestroyRef);
  readonly kind = inject(ActivatedRoute).snapshot.data['kind'] as InstitutionKind;
  readonly title = this.kind === 'areas' ? 'Áreas' : 'Cargos';
  readonly items = signal<Institution[]>([]);
  readonly editing = signal<number | null>(null);
  readonly loading = signal(false);
  readonly busy = signal(false);
  readonly error = signal('');
  readonly notice = signal('');
  readonly form = inject(FormBuilder).nonNullable.group({
    nombre: ['', [Validators.required, Validators.maxLength(150)]],
    descripcion: ['', Validators.maxLength(5000)],
  });
  constructor() {
    this.load();
  }
  /**
   * Carga todos los estados del catálogo y actualiza listado o error; también se usa después
   * de guardar.
   */
  load() {
    this.loading.set(true);
    this.error.set('');
    this.api
      .institution(this.kind)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (items) => this.items.set(items),
        error: (e) => this.error.set(apiError(e)),
      });
  }
  /**
   * Copia un registro al formulario y guarda su ID para que save realice PATCH; todavía no
   * escribe en servidor.
   */
  edit(item: Institution) {
    this.editing.set(item.id);
    this.form.patchValue(item);
    this.error.set('');
  }
  /**
   * Limpia selección y formulario para volver al alta; no modifica el catálogo remoto.
   */
  cancel() {
    this.editing.set(null);
    this.form.reset();
  }
  /**
   * Valida nombre/descripcion, crea o edita según editing y recarga listado al éxito. Busy
   * impide envíos repetidos; los errores conservan el formulario.
   */
  save() {
    this.form.markAllAsTouched();
    if (this.form.invalid || this.busy()) return;
    this.busy.set(true);
    this.error.set('');
    this.notice.set('');
    this.api
      .saveInstitution(this.kind, this.editing(), this.form.getRawValue())
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.busy.set(false)),
      )
      .subscribe({
        next: () => {
          this.cancel();
          this.notice.set('Registro guardado.');
          this.load();
        },
        error: (e) => this.error.set(apiError(e)),
      });
  }
  /**
   * Confirma el cambio de activo del registro, solicita la acción y recarga. No borra el
   * catálogo ni desvincula personas.
   */
  toggle(item: Institution) {
    if (this.busy() || !window.confirm(`${item.activo ? 'Desactivar' : 'Activar'} ${item.nombre}?`))
      return;
    this.busy.set(true);
    this.error.set('');
    this.api
      .institutionActive(this.kind, item.id, !item.activo)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.busy.set(false)),
      )
      .subscribe({
        next: () => {
          this.notice.set('Estado actualizado.');
          this.load();
        },
        error: (e) => this.error.set(apiError(e)),
      });
  }
}

@Component({
  selector: 'app-institution',
  imports: [ReactiveFormsModule],
  providers: [InstitutionViewModel],
  template: `
    <p class="eyebrow">SUPERADMIN / INSTITUCIÓN</p>
    <h1>{{ vm.title }}</h1>
    <p>Administra las opciones institucionales disponibles al registrar personas.</p>
    @if (vm.error()) {
      <p class="sa-error" role="alert">
        {{ vm.error() }} <button (click)="vm.load()">Reintentar</button>
      </p>
    }
    @if (vm.notice()) {
      <p class="sa-success" role="status">{{ vm.notice() }}</p>
    }
    <form class="sa-panel" [formGroup]="vm.form" (ngSubmit)="vm.save()">
      <h2>{{ vm.editing() ? 'Editar registro' : 'Nuevo registro' }}</h2>
      <div class="sa-form-grid">
        <label
          >Nombre *<input formControlName="nombre" maxlength="150" />
          @if (vm.form.controls.nombre.touched && vm.form.controls.nombre.invalid) {
            <small class="sa-field-error">El nombre es obligatorio.</small>
          }
        </label>
        <label
          >Descripción<textarea formControlName="descripcion" rows="2" maxlength="5000"></textarea>
        </label>
      </div>
      <div class="sa-actions">
        <button class="button button-small" [disabled]="vm.busy()">Guardar</button>
        @if (vm.editing()) {
          <button class="button button-outline button-small" type="button" (click)="vm.cancel()">
            Cancelar edición
          </button>
        }
      </div>
    </form>
    @if (vm.loading()) {
      <p role="status">Cargando registros…</p>
    }
    <section class="sa-panel">
      <div class="sa-table-wrap">
        <table>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Descripción</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            @for (item of vm.items(); track item.id) {
              <tr>
                <td>{{ item.nombre }}</td>
                <td>{{ item.descripcion || '—' }}</td>
                <td>
                  <span class="sa-badge" [class.inactive]="!item.activo">{{
                    item.activo ? 'Activo' : 'Inactivo'
                  }}</span>
                </td>
                <td>
                  <div class="sa-row-actions">
                    <button (click)="vm.edit(item)" [disabled]="vm.busy()">Editar</button
                    ><button (click)="vm.toggle(item)" [disabled]="vm.busy()">
                      {{ item.activo ? 'Desactivar' : 'Activar' }}
                    </button>
                  </div>
                </td>
              </tr>
            } @empty {
              <tr>
                <td colspan="4">Todavía no hay registros.</td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    </section>
  `,
})
/**
 * Presenta el formulario y tabla del ViewModel para ambos catálogos.
 */
export class InstitutionComponent {
  readonly vm = inject(InstitutionViewModel);
}
