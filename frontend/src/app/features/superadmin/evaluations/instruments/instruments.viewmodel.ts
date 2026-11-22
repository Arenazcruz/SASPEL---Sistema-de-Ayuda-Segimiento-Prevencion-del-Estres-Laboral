/** Estado y coordinación de T25-A; HTTP y DOM permanecen en sus adaptadores. */
import { DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, Validators } from '@angular/forms';
import { finalize, Subscription } from 'rxjs';
import { apiError } from '../../superadmin.service';
import { Instrument, InstrumentMode, InstrumentPage } from './instruments.models';
import { InstrumentsService } from './instruments.service';

@Injectable()
export class InstrumentsViewModel {
  private readonly api = inject(InstrumentsService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly fb = inject(FormBuilder);
  private listRequest?: Subscription;
  private detailRequest?: Subscription;
  private appliedFilters = { search: '', activo: '', es_inicial: '' };
  private currentPage = 1;
  readonly page = signal<InstrumentPage | null>(null);
  readonly loading = signal(false);
  readonly error = signal('');
  readonly notice = signal('');
  readonly busy = signal(false);
  readonly mode = signal<InstrumentMode | null>(null);
  readonly selected = signal<Instrument | null>(null);
  readonly detailLoading = signal(false);
  readonly modalError = signal('');
  readonly saving = signal(false);
  readonly filters = this.fb.nonNullable.group({ search: '', activo: '', es_inicial: '' });
  readonly form = this.fb.nonNullable.group({
    codigo: ['', [Validators.required, Validators.maxLength(50), Validators.pattern(/\S/)]],
    nombre: ['', [Validators.required, Validators.maxLength(200), Validators.pattern(/\S/)]],
    version: ['1.0', [Validators.required, Validators.maxLength(50), Validators.pattern(/\S/)]],
    descripcion: '',
    instrucciones: '',
    es_inicial: false,
  });

  constructor() {
    this.reload();
  }

  search() {
    this.appliedFilters = {
      ...this.filters.getRawValue(),
      search: this.filters.controls.search.value.trim(),
    };
    this.currentPage = 1;
    this.reload();
  }
  goTo(page: number) {
    if (page < 1 || this.loading()) return;
    this.currentPage = page;
    this.reload();
  }
  reload() {
    this.listRequest?.unsubscribe();
    this.loading.set(true);
    this.error.set('');
    this.listRequest = this.api
      .list({ ...this.appliedFilters, page: this.currentPage })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (page) => {
          this.page.set(page);
          if (!page.results.length && page.page > 1) {
            this.currentPage = Math.max(1, Math.ceil(page.count / page.page_size));
            // Nueva carga fuera del callback para no sobrescribir la suscripción vigente.
            queueMicrotask(() => {
              if (!this.destroyRef.destroyed) this.reload();
            });
          }
        },
        error: (error) => {
          this.page.set(null);
          this.error.set(apiError(error));
        },
      });
  }
  open(mode: InstrumentMode, instrument?: Instrument) {
    if (this.saving()) return;
    this.detailRequest?.unsubscribe();
    this.mode.set(mode);
    this.selected.set(null);
    this.modalError.set('');
    this.form.reset({
      codigo: '',
      nombre: '',
      version: '1.0',
      descripcion: '',
      instrucciones: '',
      es_inicial: false,
    });
    if (mode === 'create' || !instrument) return;
    this.detailLoading.set(true);
    this.detailRequest = this.api
      .get(instrument.id)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.detailLoading.set(false)),
      )
      .subscribe({
        next: (item) => {
          this.selected.set(item);
          this.form.patchValue(item);
        },
        error: (error) => this.modalError.set(apiError(error)),
      });
  }
  close() {
    if (this.saving()) return;
    this.detailRequest?.unsubscribe();
    this.mode.set(null);
    this.selected.set(null);
  }
  fieldError(name: string) {
    const field = this.form.get(name);
    if (!field?.touched || !field.errors) return '';
    if (field.errors['server']) return field.errors['server'] as string;
    if (field.errors['maxlength'])
      return `Máximo ${field.errors['maxlength'].requiredLength} caracteres.`;
    return 'Este campo es obligatorio y no puede contener solo espacios.';
  }
  save() {
    if (this.saving() || this.detailLoading() || !['create', 'edit'].includes(this.mode() || ''))
      return;
    const raw = this.form.getRawValue();
    this.form.patchValue({
      codigo: raw.codigo.trim(),
      nombre: raw.nombre.trim(),
      version: raw.version.trim(),
    });
    this.form.markAllAsTouched();
    if (this.form.invalid) return;
    const selected = this.selected();
    if (this.mode() === 'edit' && !selected) return;
    this.saving.set(true);
    this.modalError.set('');
    const data = this.form.getRawValue();
    const request =
      this.mode() === 'create' ? this.api.create(data) : this.api.update(selected!.id, data);
    request
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.saving.set(false)),
      )
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.close();
          this.notice.set('Instrumento guardado.');
          this.reload();
        },
        error: (error) => {
          if (error.status === 400 && error.error && typeof error.error === 'object') {
            for (const [name, message] of Object.entries(error.error)) {
              const control = this.form.get(name);
              if (control) {
                control.setErrors({
                  server: Array.isArray(message) ? message.join(' ') : String(message),
                });
                control.markAsTouched();
              }
            }
          }
          this.modalError.set(apiError(error));
        },
      });
  }
  toggle(item: Instrument) {
    if (this.busy()) return;
    this.busy.set(true);
    this.error.set('');
    this.notice.set('');
    this.api
      .active(item.id, !item.activo)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.busy.set(false)),
      )
      .subscribe({
        next: (updated) => {
          this.notice.set(updated.activo ? 'Instrumento activado.' : 'Instrumento desactivado.');
          this.reload();
        },
        error: (error) => this.error.set(apiError(error)),
      });
  }
}
