import { HttpErrorResponse } from '@angular/common/http';
import { DestroyRef, computed, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router } from '@angular/router';
import { finalize } from 'rxjs';
import { AuthService } from '../../core/auth/auth.service';
import { Politica, PrimerAccesoService } from './primer-acceso.service';

@Injectable()
export class PrimerAccesoPoliticasViewModel {
  private readonly api = inject(PrimerAccesoService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  readonly auth = inject(AuthService);
  readonly politicas = signal<Politica[]>([]);
  readonly selected = signal<Set<string>>(new Set());
  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly error = signal('');
  readonly ready = signal(false);
  readonly canAccept = computed(
    () =>
      this.ready() &&
      !this.loading() &&
      !this.saving() &&
      this.politicas().length > 0 &&
      this.politicas().every((p) => this.selected().has(p.id)),
  );

  constructor() {
    this.load();
  }

  load() {
    if (this.loading() || this.saving()) return;
    this.loading.set(true);
    this.ready.set(false);
    this.error.set('');
    this.selected.set(new Set());
    this.api
      .pendientes()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (politicas) => {
          this.politicas.set(politicas);
          this.ready.set(true);
          if (!politicas.length) this.continue();
        },
        error: () => this.error.set('No se pudieron cargar las políticas. Inténtalo de nuevo.'),
      });
  }

  select(id: string, checked: boolean) {
    const selected = new Set(this.selected());
    if (checked) selected.add(id);
    else selected.delete(id);
    this.selected.set(selected);
  }

  private continue() {
    this.api
      .estado()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (estado) => {
          if (estado.siguiente_ruta === '/primer-acceso/politicas') {
            this.ready.set(false);
            this.error.set('Las políticas cambiaron. Vuelve a cargarlas para revisarlas.');
          } else void this.router.navigateByUrl(estado.siguiente_ruta);
        },
        error: () => this.error.set('No se pudo verificar tu estado. Inténtalo de nuevo.'),
      });
  }

  submit() {
    if (!this.canAccept()) return;
    this.saving.set(true);
    this.error.set('');
    this.api
      .aceptar(this.politicas().map((p) => p.id))
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.saving.set(false)),
      )
      .subscribe({
        next: (estado) => {
          if (estado.siguiente_ruta === '/primer-acceso/politicas') {
            this.ready.set(false);
            this.selected.set(new Set());
            this.error.set('Hay nuevas políticas pendientes. Vuelve a cargarlas para revisarlas.');
          } else void this.router.navigateByUrl(estado.siguiente_ruta);
        },
        error: (error: HttpErrorResponse) => {
          if (error.error?.politicas) {
            this.ready.set(false);
            this.selected.set(new Set());
            this.error.set(
              'Las políticas cambiaron. Vuelve a cargarlas para revisar las versiones vigentes.',
            );
          } else
            this.error.set(
              error.error?.detail || 'No se pudo registrar la aceptación. Inténtalo de nuevo.',
            );
        },
      });
  }
}
