import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { Brand } from '../../shared/brand/brand';
import { NuevoTrabajadorDashboardViewModel } from './dashboard.viewmodel';

@Component({
  selector: 'app-nuevo-trabajador-dashboard',
  imports: [Brand, DatePipe],
  providers: [NuevoTrabajadorDashboardViewModel],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class NuevoTrabajadorDashboard {
  readonly vm = inject(NuevoTrabajadorDashboardViewModel);
}
