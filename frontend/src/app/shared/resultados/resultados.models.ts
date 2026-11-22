import { InjectionToken } from '@angular/core';
import { Observable } from 'rxjs';

export interface ResultadoResumen {
  id: string;
  instrumento: string;
  version: string;
  fecha: string;
  puntaje: string;
  rango: string | null;
  interpretacion: string;
  estado: 'FINALIZADA';
}

export interface ResultadosSource {
  listar(trabajadorId?: string): Observable<ResultadoResumen[]>;
  detalle(id: string): Observable<ResultadoResumen>;
}

export const RESULTADOS_SOURCE = new InjectionToken<ResultadosSource>('ResultadosSource');
export const RESULTADOS_CONFIG = new InjectionToken<{
  titulo: string;
  vacio: string;
  volver: string;
  detalleBase: string;
}>('ResultadosConfig');
