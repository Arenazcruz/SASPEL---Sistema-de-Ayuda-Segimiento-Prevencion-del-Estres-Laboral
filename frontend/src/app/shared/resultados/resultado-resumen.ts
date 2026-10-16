import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, input } from '@angular/core';
import { ResultadoResumen } from './resultados.models';

@Component({
  selector: 'app-resultado-resumen',
  imports: [DatePipe, DecimalPipe],
  template: `
    <h2>{{ resultado().instrumento }}</h2>
    <p>Versión {{ resultado().version }}</p>
    <dl>
      <div>
        <dt>Fecha</dt>
        <dd>{{ resultado().fecha | date: 'dd/MM/yyyy HH:mm' }}</dd>
      </div>
      <div>
        <dt>Puntaje</dt>
        <dd>{{ resultado().puntaje | number: '1.0-4' }}</dd>
      </div>
      <div>
        <dt>Nivel</dt>
        <dd>{{ resultado().rango || 'Sin clasificación configurada' }}</dd>
      </div>
      <div>
        <dt>Estado</dt>
        <dd>FINALIZADA</dd>
      </div>
    </dl>
    @if (resultado().interpretacion) {
      <h3>Interpretación</h3>
      <p>{{ resultado().interpretacion }}</p>
    }
    <p class="note">
      Este resultado es orientativo y no constituye por sí solo un diagnóstico clínico.
    </p>
  `,
  styles: [
    `
      :host {
        display: block;
        overflow-wrap: anywhere;
      }
      h2 {
        font-size: 24px;
        margin-bottom: 8px;
      }
      h3 {
        font-size: 16px;
        margin-top: 24px;
      }
      p {
        line-height: 1.7;
        white-space: pre-wrap;
      }
      dl {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 150px), 1fr));
        gap: 16px;
      }
      dt {
        color: var(--muted);
        font-size: 13px;
      }
      dd {
        margin: 6px 0 0;
        font-weight: 600;
      }
      .note {
        color: var(--muted);
        font-size: 13px;
        margin-top: 24px;
      }
    `,
  ],
})
export class ResultadoResumenComponent {
  readonly resultado = input.required<ResultadoResumen>();
}
