import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Brand } from '../../shared/brand/brand';
import { MisTrabajadoresViewModel } from './trabajadores.viewmodel';

@Component({
  selector: 'app-psicologo-dashboard',
  imports: [Brand, RouterLink],
  providers: [MisTrabajadoresViewModel],
  template: `
    <header class="wrap page-header">
      <app-brand />
      <div>
        <span>{{ vm.user()?.email }}</span>
        <button class="button button-outline" type="button" (click)="vm.logout()">
          Cerrar sesión
        </button>
      </div>
    </header>
    <main class="wrap content" [attr.aria-busy]="vm.loading()">
      <p class="eyebrow">MI ESPACIO · PSICÓLOGO</p>
      <h1>Bienvenido/a, {{ vm.nombre() }}</h1>
      <section class="card" aria-labelledby="workers-title">
        <h2 id="workers-title">Mis trabajadores</h2>
        @if (vm.loading()) {
          <p role="status">Consultando asignaciones…</p>
        } @else if (vm.error()) {
          <p class="error" role="alert">{{ vm.error() }}</p>
          <button class="button button-outline" type="button" (click)="vm.load()">
            Reintentar
          </button>
        } @else if (vm.datos(); as datos) {
          <p>
            <strong>{{ datos.cantidad }}</strong> asignaciones profesionales activas
          </p>
          @if (!datos.cantidad) {
            <p>No tienes trabajadores asignados actualmente.</p>
          }
          <p>Consulta los resultados disponibles de tus trabajadores asignados.</p>
          <a class="button" routerLink="/dashboard/psicologo/trabajadores">Mis trabajadores</a>
        }
      </section>
    </main>
  `,
  styleUrl: '../../shared/resultados/consulta.scss',
  styles: [
    '.page-header > div { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; overflow-wrap: anywhere; }',
  ],
})
export class PsicologoDashboard {
  readonly vm = inject(MisTrabajadoresViewModel);
}
