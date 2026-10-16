import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { throwError } from 'rxjs';
import { API_URL } from '../../core/auth/api-url';
import { ResultadoResumen, ResultadosSource } from '../../shared/resultados/resultados.models';
import { MisTrabajadores } from './psicologo.models';

@Injectable({ providedIn: 'root' })
export class PsicologoService implements ResultadosSource {
  private readonly http = inject(HttpClient);
  private readonly base = `${inject(API_URL)}/psicologo/`;
  trabajadores() {
    return this.http.get<MisTrabajadores>(`${this.base}trabajadores/`);
  }
  listar(trabajadorId?: string) {
    if (!trabajadorId) return throwError(() => new Error('Selecciona un trabajador.'));
    return this.http.get<ResultadoResumen[]>(
      `${this.base}trabajadores/${encodeURIComponent(trabajadorId)}/resultados/`,
    );
  }
  detalle(id: string) {
    return this.http.get<ResultadoResumen>(`${this.base}resultados/${encodeURIComponent(id)}/`);
  }
}
