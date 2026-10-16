import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Brand } from '../../shared/brand/brand';
import { ResultadoResumenComponent } from '../../shared/resultados/resultado-resumen';
import { RESULTADOS_CONFIG, RESULTADOS_SOURCE } from '../../shared/resultados/resultados.models';
import { ResultadosViewModel } from '../../shared/resultados/resultados.viewmodel';
import { PsicologoService } from './psicologo.service';

@Component({
  selector: 'app-psicologo-resultados',
  imports: [Brand, RouterLink, ResultadoResumenComponent],
  providers: [
    ResultadosViewModel,
    { provide: RESULTADOS_SOURCE, useExisting: PsicologoService },
    {
      provide: RESULTADOS_CONFIG,
      useValue: {
        titulo: 'Resultados del trabajador',
        vacio: 'Este trabajador aún no tiene resultados disponibles.',
        volver: '/dashboard/psicologo',
        detalleBase: '/dashboard/psicologo/resultados',
      },
    },
  ],
  templateUrl: '../../shared/resultados/resultados.html',
  styleUrl: '../../shared/resultados/consulta.scss',
})
export class PsicologoResultados {
  readonly vm = inject(ResultadosViewModel);
}
