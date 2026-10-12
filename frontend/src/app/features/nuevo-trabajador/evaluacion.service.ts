import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { API_URL } from '../../core/auth/api-url';
import { EvaluacionDetalle, RespuestaEvaluacion } from './evaluacion.models';

@Injectable({ providedIn: 'root' })
export class EvaluacionService {
  private readonly http = inject(HttpClient);
  private readonly base = `${inject(API_URL)}/nuevo-trabajador/evaluaciones/`;

  consultar(id: string) {
    return this.http.get<EvaluacionDetalle>(`${this.base}${id}/`);
  }
  iniciar(id: string) {
    return this.http.post<EvaluacionDetalle>(`${this.base}${id}/iniciar/`, {});
  }
  guardar(id: string, respuestas: RespuestaEvaluacion[]) {
    return this.http.post<EvaluacionDetalle>(`${this.base}${id}/respuestas/`, { respuestas });
  }
  finalizar(id: string, respuestas: RespuestaEvaluacion[]) {
    return this.http.post<EvaluacionDetalle>(`${this.base}${id}/finalizar/`, { respuestas });
  }
}
