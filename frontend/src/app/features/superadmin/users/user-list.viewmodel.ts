/**
 * Coordina listado y catálogos mediante SuperadminService. Ruta y query params son la fuente
 * de filtros/página; switchMap evita que búsquedas antiguas sustituyan resultados nuevos.
 * Cambiar filtros junto a UserFilters y UserFilterSerializer del backend.
 */
import { DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { catchError, combineLatest, finalize, forkJoin, of, switchMap, tap } from 'rxjs';
import { AuthService } from '../../../core/auth/auth.service';
import { Institution, Person, ROLES, UserPage } from '../superadmin.models';
import { apiError, SuperadminService } from '../superadmin.service';

@Injectable()
export class UserListViewModel {
  private readonly api = inject(SuperadminService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  readonly currentUser = inject(AuthService).user;
  readonly roles = ROLES;
  readonly page = signal<UserPage | null>(null);
  readonly areas = signal<Institution[]>([]);
  readonly cargos = signal<Institution[]>([]);
  readonly loading = signal(false);
  readonly busy = signal(false);
  readonly error = signal('');
  readonly notice = signal('');
  readonly title = signal('Usuarios');
  readonly fixedRole = signal('');
  readonly filters = inject(FormBuilder).nonNullable.group({
    search: '',
    role: '',
    active: '',
    area: '',
    cargo: '',
  });

  /**
   * Carga catálogos y suscribe datos/query params de ruta; cada cambio solicita una página y
   * cancela la búsqueda anterior. Las suscripciones terminan con la vista.
   */
  constructor() {
    forkJoin({ areas: this.api.institution('areas'), cargos: this.api.institution('cargos') })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (data) => {
          this.areas.set(data.areas);
          this.cargos.set(data.cargos);
        },
        error: (e) => this.error.set(apiError(e)),
      });
    // switchMap cancela búsquedas anteriores para que una respuesta tardía no cambie el filtro visible.
    combineLatest([this.route.data, this.route.queryParamMap])
      .pipe(
        tap(([data, params]) => {
          this.title.set(data['title'] || 'Usuarios');
          this.fixedRole.set(data['filterRole'] || '');
          this.filters.patchValue({
            search: params.get('search') || '',
            role: this.fixedRole() || params.get('role') || '',
            active: params.get('active') || '',
            area: params.get('area') || '',
            cargo: params.get('cargo') || '',
          });
        }),
        switchMap(([, params]) => {
          this.loading.set(true);
          this.error.set('');
          return this.api
            .users({
              ...this.filters.getRawValue(),
              page: Math.max(1, Number(params.get('page')) || 1),
            })
            .pipe(
              catchError((error) => {
                this.error.set(apiError(error));
                return of(null);
              }),
              finalize(() => this.loading.set(false)),
            );
        }),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((page) => this.page.set(page));
  }
  /**
   * Recibe página (1 por defecto) y escribe filtros en la URL; la suscripción de ruta realiza
   * la consulta.
   */
  search(page = 1) {
    this.notice.set('');
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { ...this.filters.getRawValue(), page },
    });
  }
  /**
   * Recarga filtros y página actuales tras una acción; actualiza resultados, carga o error sin
   * navegar.
   */
  reload() {
    this.loading.set(true);
    this.api
      .users({ ...this.filters.getRawValue(), page: this.page()?.page || 1 })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (page) => this.page.set(page),
        error: (e) => this.error.set(apiError(e)),
      });
  }
  /**
   * Recibe persona, pide confirmación y envía activación/desactivación. Evita acciones
   * simultáneas, muestra resultado y recarga listado; las restricciones se validan en backend.
   */
  toggle(user: Person) {
    if (
      this.busy() ||
      !window.confirm(`${user.is_active ? 'Desactivar' : 'Activar'} a ${user.email}?`)
    )
      return;
    this.busy.set(true);
    this.error.set('');
    this.api
      .active(user.id, !user.is_active)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.busy.set(false)),
      )
      .subscribe({
        next: () => {
          this.notice.set(user.is_active ? 'Usuario desactivado.' : 'Usuario activado.');
          this.reload();
        },
        error: (e) => this.error.set(apiError(e)),
      });
  }
}
