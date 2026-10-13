import { Component, ElementRef, inject, input, output } from '@angular/core';
import { PreguntaEvaluacion, ValorRespuesta } from './evaluacion.models';

/** Presentación de una pregunta sin dependencias de rol, sesión ni servicios. */
@Component({
  selector: 'app-evaluacion-pregunta',
  template: `
    <fieldset
      [disabled]="disabled()"
      [attr.id]="'pregunta-' + pregunta().id"
      [attr.aria-describedby]="pendiente() ? 'pendiente-' + pregunta().id : null"
    >
      <legend>
        {{ pregunta().orden }}. {{ pregunta().texto }}
        @if (pregunta().obligatoria) {
          <span class="required">Obligatoria</span>
        }
      </legend>
      @switch (pregunta().tipo_respuesta) {
        @case ('ESCALA') {
          @for (opcion of pregunta().opciones; track opcion.id) {
            <label class="choice"
              ><input
                type="radio"
                [name]="pregunta().id"
                [checked]="valor() === opcion.id"
                (change)="valorChange.emit(opcion.id)"
              />{{ opcion.etiqueta }}</label
            >
          }
        }
        @case ('TEXTO') {
          <textarea
            rows="4"
            maxlength="20000"
            [attr.aria-label]="pregunta().texto"
            [value]="valor() ?? ''"
            (input)="texto($event)"
          ></textarea>
        }
        @case ('NUMERO') {
          <input
            type="number"
            step="0.0001"
            min="-99999999.9999"
            max="99999999.9999"
            [attr.aria-label]="pregunta().texto"
            [value]="valor() ?? ''"
            (input)="texto($event)"
          />
        }
        @case ('BOOLEANO') {
          <label class="choice"
            ><input
              type="radio"
              [name]="pregunta().id"
              [checked]="valor() === true"
              (change)="valorChange.emit(true)"
            />Sí</label
          >
          <label class="choice"
            ><input
              type="radio"
              [name]="pregunta().id"
              [checked]="valor() === false"
              (change)="valorChange.emit(false)"
            />No</label
          >
        }
      }
      @if (valor() !== null && valor() !== '') {
        <button class="clear" type="button" (click)="valorChange.emit(null)">
          Borrar respuesta
        </button>
      }
      @if (pendiente()) {
        <p class="missing" role="alert" [id]="'pendiente-' + pregunta().id">
          Responde esta pregunta obligatoria.
        </p>
      }
    </fieldset>
  `,
  styles: [
    `
      fieldset {
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 22px;
        margin: 0 0 24px;
        min-width: 0;
      }
      legend {
        padding-inline: 6px;
        font-weight: 600;
        line-height: 1.6;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
      }
      .required {
        display: inline-block;
        font-size: 11px;
        font-weight: 400;
        margin-left: 12px;
        color: var(--muted);
      }
      .choice {
        display: flex;
        gap: 12px;
        align-items: center;
        padding: 12px 8px;
        cursor: pointer;
        overflow-wrap: anywhere;
      }
      input[type='radio'] {
        accent-color: var(--green);
        width: 18px;
        height: 18px;
        flex-shrink: 0;
      }
      textarea,
      input[type='number'] {
        width: 100%;
        font: inherit;
        color: var(--ink);
        padding: 12px;
        border: 1px solid var(--line);
        border-radius: 6px;
        background: white;
      }
      textarea {
        resize: vertical;
      }
      .clear {
        display: block;
        margin-top: 12px;
        background: none;
        border: 0;
        color: var(--green);
        text-decoration: underline;
        cursor: pointer;
      }
      .missing {
        color: #963b2f;
        font-size: 13px;
      }
      :disabled {
        cursor: default;
      }
    `,
  ],
})
export class EvaluacionPregunta {
  private readonly element = inject<ElementRef<HTMLElement>>(ElementRef);
  readonly pregunta = input.required<PreguntaEvaluacion>();
  readonly valor = input<ValorRespuesta>(null);
  readonly disabled = input(false);
  readonly pendiente = input(false);
  readonly valorChange = output<ValorRespuesta>();
  focus(): void {
    this.element.nativeElement
      .querySelector<HTMLElement>('input:not(:disabled), textarea:not(:disabled)')
      ?.focus();
  }
  texto(event: Event): void {
    this.valorChange.emit((event.target as HTMLInputElement).value || null);
  }
}
