import { Component, inject } from '@angular/core';
import { Brand } from '../../shared/brand/brand';
import { EvaluacionPregunta } from './evaluacion-pregunta';
import { EvaluacionViewModel } from './evaluacion.viewmodel';

@Component({
  selector: 'app-evaluacion-inicial',
  imports: [Brand, EvaluacionPregunta],
  providers: [EvaluacionViewModel],
  templateUrl: './evaluacion.html',
  styleUrl: './evaluacion.scss',
})
export class EvaluacionInicialComponent {
  readonly vm = inject(EvaluacionViewModel);
}
