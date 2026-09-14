/**
 * MVVM de asignaciones manuales. Mantiene filtros aplicados, formulario y estados de carga.
 * switchMap cancela lecturas antiguas; una escritura exitosa recarga listas y carga real.
 * Las reglas finales se validan siempre en backend, incluso con selectores desactualizados.
 */
import { computed, DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, Validators } from '@angular/forms';
import { BehaviorSubject, catchError, finalize, forkJoin, of, switchMap } from 'rxjs';
import { apiError } from '../superadmin.service';
import {
  AssignmentAction,
  AssignmentPage,
  AssignmentPerson,
  ProfessionalAssignment,
  PsychologistLoad,
} from './assignments.models';
import { AssignmentsService } from './assignments.service';

@Injectable()
export class AssignmentsViewModel {
  private readonly api = inject(AssignmentsService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly fb = inject(FormBuilder);
  private readonly queries = new BehaviorSubject({
    estado: 'ACTIVA',
    search: '',
    trabajador_id: '',
    page: 1,
    workerSearch: '',
    workerPage: 1,
  });
  readonly rows = signal<AssignmentPage<ProfessionalAssignment> | null>(null);
  readonly workers = signal<AssignmentPage<AssignmentPerson> | null>(null);
  readonly loads = signal<PsychologistLoad[]>([]);
  readonly loading = signal(false);
  readonly busy = signal(false);
  readonly loadError = signal('');
  readonly actionError = signal('');
  readonly notice = signal('');
  readonly selection = signal<AssignmentAction | null>(null);
  readonly historyWorker = signal<AssignmentPerson | null>(null);
  readonly filters = this.fb.nonNullable.group({ estado: 'ACTIVA', search: '' });
  readonly workerFilters = this.fb.nonNullable.group({ search: '' });
  readonly form = this.fb.nonNullable.group({
    psicologo_id: [0, Validators.min(1)],
    motivo_fin: ['', Validators.maxLength(2000)],
  });
  readonly selectedWorker = computed(() => {
    const selection = this.selection();
    return selection?.kind === 'assign' ? selection.worker : selection?.assignment.trabajador;
  });
  readonly currentPsychologist = computed(() => {
    const selection = this.selection();
    return selection && selection.kind !== 'assign' ? selection.assignment.psicologo : null;
  });
  readonly availablePsychologists = computed(() =>
    this.loads().filter(
      ({ psicologo }) =>
        psicologo.id !== this.selectedWorker()?.id &&
        psicologo.id !== this.currentPsychologist()?.id,
    ),
  );

  constructor() {
    this.queries
      .pipe(
        switchMap(({ workerSearch, workerPage, ...filters }) => {
          this.loading.set(true);
          this.loadError.set('');
          return forkJoin({
            rows: this.api.list(filters),
            workers: this.api.unassigned(workerSearch, workerPage),
            loads: this.api.psychologists(),
          }).pipe(
            catchError((error) => {
              this.loadError.set(apiError(error));
              return of(null);
            }),
            finalize(() => this.loading.set(false)),
          );
        }),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((data) => {
        this.rows.set(data?.rows ?? null);
        this.workers.set(data?.workers ?? null);
        this.loads.set(data?.loads ?? []);
      });
  }

  reload() {
    if (!this.busy()) this.queries.next({ ...this.queries.value });
  }

  search() {
    if (this.busy()) return;
    this.queries.next({ ...this.queries.value, ...this.filters.getRawValue(), page: 1 });
  }

  searchWorkers() {
    if (this.busy()) return;
    this.queries.next({
      ...this.queries.value,
      workerSearch: this.workerFilters.controls.search.value,
      workerPage: 1,
    });
  }

  page(value: number, workers = false) {
    if (this.busy() || this.loading() || value < 1) return;
    this.queries.next({ ...this.queries.value, [workers ? 'workerPage' : 'page']: value });
  }

  history(worker: AssignmentPerson | null) {
    if (this.busy()) return;
    this.historyWorker.set(worker);
    this.filters.reset({ estado: '', search: '' });
    this.queries.next({
      ...this.queries.value,
      estado: '',
      search: '',
      trabajador_id: worker ? String(worker.id) : '',
      page: 1,
    });
  }

  open(action: AssignmentAction) {
    if (this.busy() || this.loading() || this.loadError()) return;
    this.selection.set(action);
    this.actionError.set('');
    this.notice.set('');
    this.form.reset();
    this.form.controls.psicologo_id.setValidators(
      action.kind === 'finish' ? [] : [Validators.min(1)],
    );
    this.form.controls.motivo_fin.setValidators(
      action.kind === 'assign' ? [] : [Validators.required, Validators.maxLength(2000)],
    );
    this.form.controls.psicologo_id.updateValueAndValidity();
    this.form.controls.motivo_fin.updateValueAndValidity();
  }

  cancel() {
    if (this.busy()) return;
    this.selection.set(null);
    this.form.reset();
    this.actionError.set('');
  }

  submit() {
    const selection = this.selection();
    if (!selection || this.busy() || this.loading() || this.loadError()) return;
    this.form.markAllAsTouched();
    if (this.form.invalid) return;
    const { psicologo_id, motivo_fin } = this.form.getRawValue();
    if (selection.kind !== 'assign' && !motivo_fin.trim()) {
      this.actionError.set('Indica un motivo de cierre.');
      return;
    }
    if (
      selection.kind !== 'finish' &&
      !this.availablePsychologists().some((row) => row.psicologo.id === psicologo_id)
    ) {
      this.actionError.set('Selecciona un psicólogo disponible diferente al actual.');
      return;
    }
    const request =
      selection.kind === 'assign'
        ? this.api.assign(selection.worker.id, psicologo_id)
        : selection.kind === 'reassign'
          ? this.api.reassign(selection.assignment.id, psicologo_id, motivo_fin.trim())
          : this.api.finish(selection.assignment.id, motivo_fin.trim());
    this.busy.set(true);
    this.actionError.set('');
    request
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.busy.set(false)),
      )
      .subscribe({
        next: () => {
          this.notice.set(
            selection.kind === 'assign'
              ? 'Asignación creada.'
              : selection.kind === 'reassign'
                ? 'Trabajador reasignado. El vínculo anterior se conserva en el historial.'
                : 'Asignación finalizada. El trabajador queda sin asignación activa.',
          );
          this.selection.set(null);
          this.form.reset();
          this.queries.next({ ...this.queries.value, page: 1, workerPage: 1 });
        },
        // Se conserva el formulario para corregir selección/motivo o cancelar y actualizar.
        error: (error) => this.actionError.set(apiError(error)),
      });
  }
}
