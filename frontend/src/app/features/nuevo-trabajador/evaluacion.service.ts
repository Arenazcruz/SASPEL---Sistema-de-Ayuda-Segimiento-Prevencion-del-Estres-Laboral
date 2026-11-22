import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { API_URL } from '../../core/auth/api-url';
import { AuthService } from '../../core/auth/auth.service';
import { EvaluacionDetalle, RespuestaEvaluacion, ResultadoEvaluacion } from './evaluacion.models';

@Injectable({ providedIn: 'root' })
export class EvaluacionService {
  private readonly http = inject(HttpClient);
  private readonly root = inject(API_URL);
  private readonly auth = inject(AuthService);
  private get base() { return `${this.root}/${this.auth.user()?.role === 'TRABAJADOR' ? 'trabajador' : 'nuevo-trabajador'}/evaluaciones/`; }

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
    return this.http.post<ResultadoEvaluacion>(`${this.base}${id}/finalizar/`, { respuestas });
  }
}
