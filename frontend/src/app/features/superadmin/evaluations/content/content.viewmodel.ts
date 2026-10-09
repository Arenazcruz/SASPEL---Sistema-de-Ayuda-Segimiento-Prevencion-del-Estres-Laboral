import { computed, DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { finalize, forkJoin, Observable, of, Subscription } from 'rxjs';
import { apiError } from '../../superadmin.service';
import { Instrument } from '../instruments/instruments.models';
import {
  CONTENT_CONFIG,
  ContentKind,
  ContentMode,
  ContentPage,
  ContentRow,
  ContentScope,
  ContentValue,
} from './content.models';
import { InstrumentContentService } from './content.service';

@Injectable()
export class InstrumentContentViewModel {
  private readonly api = inject(InstrumentContentService);
  private readonly destroy = inject(DestroyRef);
  private readonly route = inject(ActivatedRoute);
  readonly rootKind = this.route.snapshot.data['kind'] as ContentKind;
  readonly scale = signal<ContentRow | null>(null);
  readonly kind = computed<ContentKind>(() => (this.scale() ? 'options' : this.rootKind));
  readonly config = computed(() => CONTENT_CONFIG[this.kind()]);
  readonly instrumentId = signal(this.route.snapshot.queryParamMap.get('instrumento') ?? '');
  readonly instruments = signal<Instrument[]>([]);
  readonly scales = signal<ContentRow[]>([]);
  readonly ready = signal(false);
  readonly page = signal<ContentPage | null>(null);
  readonly loading = signal(false);
  readonly busy = signal(false);
  readonly saving = signal(false);
  readonly error = signal('');
  readonly catalogError = signal('');
  readonly notice = signal('');
  readonly mode = signal<ContentMode | null>(null);
  readonly selected = signal<ContentRow | null>(null);
  readonly detailLoading = signal(false);
  readonly modalError = signal('');
  readonly needsInstrument = computed(
    () => this.kind() === 'questions' || this.kind() === 'ranges',
  );
  readonly canManage = computed(
    () => this.ready() && (!this.needsInstrument() || !!this.instrumentId()),
  );
  readonly filters = new FormGroup({
    search: new FormControl('', { nonNullable: true }),
    activo: new FormControl('', { nonNullable: true }),
  });
  form = new FormGroup<Record<string, FormControl<ContentValue>>>({});
  private listRequest?: Subscription;
  private detailRequest?: Subscription;
  private catalogRequest?: Subscription;
  private currentPage = 1;
  private applied = { search: '', activo: '' };

  constructor() {
    this.loadCatalogs();
  }

  loadCatalogs() {
    this.catalogRequest?.unsubscribe();
    this.ready.set(false);
    this.catalogError.set('');
    this.catalogRequest = forkJoin({
      instruments: this.rootKind === 'scales' ? of([] as Instrument[]) : this.api.instruments(),
      scales: this.rootKind === 'questions' ? this.api.scales() : of([] as ContentRow[]),
    })
      .pipe(takeUntilDestroyed(this.destroy))
      .subscribe({
        next: ({ instruments, scales }) => {
          this.instruments.set(instruments);
          this.scales.set(scales);
          if (this.instrumentId() && !instruments.some((item) => item.id === this.instrumentId()))
            this.instrumentId.set('');
          this.ready.set(true);
          this.reload();
        },
        error: (error) => this.catalogError.set(apiError(error)),
      });
  }
  scope(): ContentScope {
    return { kind: this.kind(), parentId: this.scale()?.id ?? (this.instrumentId() || undefined) };
  }
  chooseInstrument(id: string) {
    if (this.busy() || this.saving()) return;
    this.close();
    this.instrumentId.set(id);
    this.currentPage = 1;
    this.notice.set('');
    this.reload();
  }
  openOptions(scale: ContentRow) {
    if (this.busy() || this.saving()) return;
    this.close();
    this.scale.set(scale);
    this.resetList();
  }
  backToScales() {
    if (this.busy() || this.saving()) return;
    this.close();
    this.scale.set(null);
    this.resetList();
  }
  private resetList() {
    this.filters.reset({ search: '', activo: '' });
    this.applied = { search: '', activo: '' };
    this.currentPage = 1;
    this.notice.set('');
    this.reload();
  }
  search() {
    if (this.busy() || this.saving()) return;
    this.applied = {
      ...this.filters.getRawValue(),
      search: this.filters.controls.search.value.trim(),
    };
    this.currentPage = 1;
    this.reload();
  }
  goTo(page: number) {
    if (page < 1 || this.loading() || this.busy() || this.saving()) return;
    this.currentPage = page;
    this.reload();
  }
  reload() {
    this.listRequest?.unsubscribe();
    this.page.set(null);
    this.error.set('');
    if (!this.canManage()) return;
    this.loading.set(true);
    this.listRequest = this.api
      .list(this.scope(), { ...this.applied, page: this.currentPage })
      .pipe(
        takeUntilDestroyed(this.destroy),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (page) => {
          this.page.set(page);
          if (!page.results.length && page.page > 1) {
            this.currentPage = Math.max(1, Math.ceil(page.count / page.page_size));
            queueMicrotask(() => {
              if (!this.destroy.destroyed) this.reload();
            });
          }
        },
        error: (error) => this.error.set(apiError(error)),
      });
  }
  open(mode: ContentMode, row?: ContentRow) {
    if (!this.canManage() || this.busy() || this.saving() || this.loading()) return;
    this.detailRequest?.unsubscribe();
    this.mode.set(mode);
    this.selected.set(null);
    this.modalError.set('');
    this.makeForm();
    if (mode === 'create' || !row) return;
    this.detailLoading.set(true);
    this.detailRequest = this.api
      .get(this.scope(), row.id)
      .pipe(
        takeUntilDestroyed(this.destroy),
        finalize(() => this.detailLoading.set(false)),
      )
      .subscribe({
        next: (item) => {
          this.selected.set(item);
          this.makeForm(item);
        },
        error: (error) => this.modalError.set(apiError(error)),
      });
  }
  private makeForm(row?: ContentRow) {
    const controls: Record<string, FormControl<ContentValue>> = {};
    for (const field of this.config().fields) {
      const validators = [];
      if (field.required) validators.push(Validators.required);
      if (field.required && ['text', 'textarea'].includes(field.type))
        validators.push(Validators.pattern(/\S/));
      if (field.maxLength) validators.push(Validators.maxLength(field.maxLength));
      if (field.min !== undefined) validators.push(Validators.min(field.min));
      if (field.max !== undefined) validators.push(Validators.max(field.max));
      if (field.type === 'number') validators.push(Validators.pattern(/^-?\d+$/));
      controls[field.name] = new FormControl<ContentValue>(
        row ? (row[field.name as keyof ContentRow] ?? field.initial) : field.initial,
        validators,
      );
    }
    this.form = new FormGroup(controls);
    this.form.setValidators((form) => {
      const value = form.getRawValue();
      if (
        this.kind() === 'questions' &&
        value['tipo_respuesta'] === 'ESCALA' &&
        !value['escala_id']
      )
        return { scaleRequired: true };
      if (
        this.kind() === 'ranges' &&
        Number(value['puntaje_minimo']) > Number(value['puntaje_maximo'])
      )
        return { range: true };
      return null;
    });
  }
  close() {
    if (this.saving()) return;
    this.detailRequest?.unsubscribe();
    this.mode.set(null);
    this.selected.set(null);
  }
  scaleAllowed(row: ContentRow) {
    return row.activo || row.id === this.selected()?.escala_id;
  }
  scaleName(id: string | null | undefined) {
    return this.scales().find((row) => row.id === id)?.nombre ?? 'Sin escala';
  }
  fieldError(name: string) {
    const control = this.form.get(name);
    if (!control?.touched || !control.errors) return '';
    if (control.errors['server']) return String(control.errors['server']);
    if (control.errors['min'] || control.errors['max'] || control.errors['pattern'])
      return 'Revisa el formato o el intervalo permitido.';
    if (control.errors['maxlength'])
      return `Máximo ${control.errors['maxlength'].requiredLength} caracteres.`;
    return 'Este campo es obligatorio.';
  }
  save() {
    if (this.saving() || this.detailLoading() || !['create', 'edit'].includes(this.mode() ?? ''))
      return;
    if (this.mode() === 'edit' && !this.selected()) return;
    const data = this.form.getRawValue();
    for (const [name, value] of Object.entries(data))
      if (typeof value === 'string') data[name] = value.trim();
    if (this.kind() === 'questions' && data['tipo_respuesta'] !== 'ESCALA')
      data['escala_id'] = null;
    this.form.patchValue(data);
    this.form.markAllAsTouched();
    if (this.form.invalid) return;
    this.saving.set(true);
    this.modalError.set('');
    const request =
      this.mode() === 'create'
        ? this.api.create(this.scope(), data)
        : this.api.update(this.scope(), this.selected()!.id, data);
    request
      .pipe(
        takeUntilDestroyed(this.destroy),
        finalize(() => this.saving.set(false)),
      )
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.close();
          this.notice.set('Registro guardado.');
          this.reload();
        },
        error: (error) => {
          if (error.status === 400 && error.error && typeof error.error === 'object') {
            for (const [name, messages] of Object.entries(error.error)) {
              this.form
                .get(name)
                ?.setErrors({
                  server: Array.isArray(messages) ? messages.join(' ') : String(messages),
                });
            }
          }
          this.modalError.set(apiError(error));
        },
      });
  }
  toggle(row: ContentRow) {
    if (this.busy() || this.saving() || this.loading()) return;
    this.mutate(
      this.api.active(this.scope(), row.id, !row.activo),
      row.activo ? 'Registro desactivado.' : 'Registro activado.',
    );
  }
  move(row: ContentRow, direction: 'up' | 'down') {
    if (this.busy() || this.saving() || this.loading()) return;
    this.mutate(this.api.move(this.scope(), row.id, direction), 'Orden actualizado.');
  }
  private mutate(request: Observable<ContentRow>, message: string) {
    this.busy.set(true);
    this.error.set('');
    this.notice.set('');
    request
      .pipe(
        takeUntilDestroyed(this.destroy),
        finalize(() => this.busy.set(false)),
      )
      .subscribe({
        next: () => {
          this.notice.set(message);
          this.reload();
        },
        error: (error) => this.error.set(apiError(error)),
      });
  }
}
