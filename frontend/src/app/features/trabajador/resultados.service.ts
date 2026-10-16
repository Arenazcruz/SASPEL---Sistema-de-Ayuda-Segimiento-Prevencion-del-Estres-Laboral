import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { API_URL } from '../../core/auth/api-url';
import { ResultadoResumen, ResultadosSource } from '../../shared/resultados/resultados.models';

@Injectable({ providedIn: 'root' })
export class TrabajadorResultadosService implements ResultadosSource {
  private readonly http = inject(HttpClient);
  private readonly base = `${inject(API_URL)}/trabajador/resultados/`;
  listar() {
    return this.http.get<ResultadoResumen[]>(this.base);
  }
  detalle(id: string) {
    return this.http.get<ResultadoResumen>(`${this.base}${encodeURIComponent(id)}/`);
  }
}
