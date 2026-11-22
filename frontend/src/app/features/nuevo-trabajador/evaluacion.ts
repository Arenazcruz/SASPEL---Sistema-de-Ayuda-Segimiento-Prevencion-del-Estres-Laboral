import { afterRenderEffect, Component, inject, viewChildren } from '@angular/core';
import { DatePipe } from '@angular/common';
import { Brand } from '../../shared/brand/brand';
import { EvaluacionPregunta } from './evaluacion-pregunta';
import { EvaluacionViewModel } from './evaluacion.viewmodel';

@Component({
  selector: 'app-evaluacion-inicial',
  imports: [Brand, EvaluacionPregunta, DatePipe],
  providers: [EvaluacionViewModel],
  templateUrl: './evaluacion.html',
  styleUrl: './evaluacion.scss',
})
export class EvaluacionInicialComponent {
  readonly vm = inject(EvaluacionViewModel);
  private readonly preguntas = viewChildren(EvaluacionPregunta);

  constructor() {
    afterRenderEffect(() => {
      const pending = this.vm.focoPendiente();
      const question = pending && this.preguntas().find((p) => p.pregunta().id === pending.id);
      if (question) {
        question.focus();
        this.vm.focoPendiente.set(null);
      }
    });
  }
}
