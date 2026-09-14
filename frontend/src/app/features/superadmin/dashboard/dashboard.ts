/**
 * Inicio de Superadmin: SuperadminDashboardViewModel carga estadísticas y recientes con
 * SuperadminService y el componente los presenta. No calcula totales localmente; revisar cards
 * para etiquetas y repositorio Django summary para criterios.
 */
import { DatePipe } from '@angular/common';
import { Component, DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { Summary } from '../superadmin.models';
import { apiError, SuperadminService } from '../superadmin.service';
import { RoleBadge } from '../shared/role-badge';

@Injectable()
/**
 * Estado de estadísticas y carga; cards vincula claves del DTO con etiquetas visibles.
 */
export class SuperadminDashboardViewModel {
  private readonly api = inject(SuperadminService);
  private readonly destroyRef = inject(DestroyRef);
  readonly summary = signal<Summary | null>(null);
  readonly loading = signal(false);
  readonly error = signal('');
  readonly cards: [keyof Omit<Summary, 'recent_users'>, string][] = [
    ['users_total', 'Usuarios totales'],
    ['new_workers', 'Nuevos trabajadores'],
    ['workers', 'Trabajadores'],
    ['psychologists', 'Psicólogos'],
    ['admins', 'Administradores'],
    ['superadmins', 'Superadmins'],
    ['active_users', 'Usuarios activos'],
    ['inactive_users', 'Usuarios inactivos'],
  ];
  constructor() {
    this.load();
  }
  /**
   * Suscribe summary del servicio y actualiza cifras, carga o error. Se usa al iniciar y al
   * reintentar; no calcula estadísticas.
   */
  load() {
    this.loading.set(true);
    this.error.set('');
    this.api
      .summary()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (value) => this.summary.set(value),
        error: (error) => this.error.set(apiError(error)),
      });
  }
}

@Component({
  selector: 'app-superadmin-dashboard',
  imports: [DatePipe, RouterLink, RoleBadge],
  providers: [SuperadminDashboardViewModel],
  template: `
    <div class="sa-heading">
      <div>
        <p class="eyebrow">SUPERADMIN / INICIO</p>
        <h1>Administración de SASPEL</h1>
        <p>Gestiona las personas y la estructura de la institución.</p>
      </div>
      <a class="button" routerLink="personas/nuevo">Registrar persona</a>
    </div>
    @if (vm.error()) {
      <div class="sa-error" role="alert">
        {{ vm.error() }} <button (click)="vm.load()">Reintentar</button>
      </div>
    }
    @if (vm.loading()) {
      <p role="status">Cargando estadísticas…</p>
    }
    @if (vm.summary(); as summary) {
      <div class="sa-stats">
        @for (card of vm.cards; track card[0]) {
          <article class="sa-panel">
            <span>{{ card[1] }}</span
            ><strong>{{ summary[card[0]] }}</strong>
          </article>
        }
      </div>
      <section class="sa-panel">
        <div class="sa-heading">
          <h2>Usuarios registrados recientemente</h2>
          <a routerLink="personas" class="text-link">Ver usuarios →</a>
        </div>
        <div class="sa-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Correo</th>
                <th>Rol</th>
                <th>Registro</th>
              </tr>
            </thead>
            <tbody>
              @for (user of summary.recent_users; track user.id) {
                <tr>
                  <td>
                    <a [routerLink]="['personas', user.id]">{{
                      user.nombre_completo || user.email
                    }}</a>
                  </td>
                  <td>{{ user.email }}</td>
                  <td><app-role-badge [role]="user.role" /></td>
                  <td>{{ user.fecha_registro | date: 'dd/MM/yyyy HH:mm' }}</td>
                </tr>
              } @empty {
                <tr>
                  <td colspan="4">No hay usuarios registrados.</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </section>
    }
  `,
})
/**
 * Presenta las tarjetas y recientes del ViewModel y enlaces a personas.
 */
export class SuperadminDashboard {
  readonly vm = inject(SuperadminDashboardViewModel);
}
