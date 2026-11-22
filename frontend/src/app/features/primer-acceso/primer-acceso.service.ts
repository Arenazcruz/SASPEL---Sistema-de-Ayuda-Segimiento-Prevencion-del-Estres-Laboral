import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { API_URL } from '../../core/auth/api-url';
import { PrimerAccesoEstado } from '../../core/auth/auth.models';

export interface Politica {
  id: string;
  tipo: string;
  titulo: string;
  version: string;
  contenido: string;
  vigente_desde: string;
  obligatoria: boolean;
  activo: boolean;
}

@Injectable({ providedIn: 'root' })
export class PrimerAccesoService {
  private readonly http = inject(HttpClient);
  private readonly base = inject(API_URL) + '/auth/primer-acceso';

  estado() {
    return this.http.get<PrimerAccesoEstado>(`${this.base}/`);
  }
  cambiarPassword(data: { password: string; password_confirmation: string }) {
    return this.http.post<PrimerAccesoEstado>(`${this.base}/password/`, data);
  }
  pendientes() {
    return this.http.get<Politica[]>(`${this.base}/politicas/`);
  }
  aceptar(politicas: string[]) {
    return this.http.post<PrimerAccesoEstado>(`${this.base}/aceptar/`, { politicas });
  }
}
