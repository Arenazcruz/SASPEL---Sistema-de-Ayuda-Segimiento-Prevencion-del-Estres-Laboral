import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Brand } from '../../shared/brand/brand';
import { MisTrabajadoresViewModel } from './trabajadores.viewmodel';

@Component({
  selector: 'app-psicologo-trabajadores',
  imports: [DatePipe, Brand, RouterLink],
  providers: [MisTrabajadoresViewModel],
  template: `
    <header class="wrap page-header">
      <app-brand />
      <a class="button button-outline" routerLink="/dashboard/psicologo">Volver a mi panel</a>
    </header>
    <main class="wrap content" [attr.aria-busy]="vm.loading()">
      <p class="eyebrow">ASIGNACIONES PROFESIONALES ACTIVAS</p>
      <h1>Mis trabajadores</h1>
      @if (vm.loading()) {
        <p role="status">Cargando trabajadores…</p>
      } @else if (vm.error()) {
        <p class="error" role="alert">{{ vm.error() }}</p>
        <button class="button button-outline" type="button" (click)="vm.load()">Reintentar</button>
      } @else if (vm.datos(); as datos) {
        @if (!datos.trabajadores.length) {
          <p class="card" role="status">No tienes trabajadores asignados actualmente.</p>
        } @else {
          <div class="results">
            @for (trabajador of datos.trabajadores; track trabajador.id) {
              <article class="card">
                <h2>{{ trabajador.nombre_completo }}</h2>
                <p>{{ trabajador.email }}</p>
                <p>Área: {{ trabajador.area || 'Sin área registrada' }}</p>
                <p>Cargo: {{ trabajador.cargo || 'Sin cargo registrado' }}</p>
                <p>
                  Asignación: {{ trabajador.fecha_asignacion | date: 'dd/MM/yyyy' }} ·
                  {{ trabajador.estado }}
                </p>
                <a
                  class="button button-outline"
                  [routerLink]="['/dashboard/psicologo/trabajadores', trabajador.id, 'resultados']"
                  [attr.aria-label]="'Ver resultados de ' + trabajador.nombre_completo"
                  >Ver resultados</a
                >
                <a class="button button-outline" [routerLink]="['/dashboard/psicologo/trabajadores', trabajador.id, 'seguimiento']">Ver seguimiento</a>
                <a class="button button-outline" [routerLink]="['/dashboard/psicologo/trabajadores', trabajador.id, 'animo']">Ver ánimo</a>
              </article>
            }
          </div>
        }
      }
    </main>
  `,
  styleUrl: '../../shared/resultados/consulta.scss',
})
export class PsicologoTrabajadores {
  readonly vm = inject(MisTrabajadoresViewModel);
}
