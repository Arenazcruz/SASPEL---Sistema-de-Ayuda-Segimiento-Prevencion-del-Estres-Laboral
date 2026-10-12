import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { API_URL } from '../../core/auth/api-url';
import { DashboardResumen } from './dashboard.models';

@Injectable({ providedIn: 'root' })
export class NuevoTrabajadorService {
  private readonly http = inject(HttpClient);
  private readonly api = inject(API_URL);

  resumen() {
    return this.http.get<DashboardResumen>(`${this.api}/nuevo-trabajador/dashboard/`);
  }
}
