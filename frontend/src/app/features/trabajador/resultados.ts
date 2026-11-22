import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Brand } from '../../shared/brand/brand';
import { ResultadoResumenComponent } from '../../shared/resultados/resultado-resumen';
import { RESULTADOS_CONFIG, RESULTADOS_SOURCE } from '../../shared/resultados/resultados.models';
import { ResultadosViewModel } from '../../shared/resultados/resultados.viewmodel';
import { TrabajadorResultadosService } from './resultados.service';

@Component({
  selector: 'app-trabajador-resultados',
  imports: [Brand, RouterLink, ResultadoResumenComponent],
  providers: [
    ResultadosViewModel,
    { provide: RESULTADOS_SOURCE, useExisting: TrabajadorResultadosService },
    {
      provide: RESULTADOS_CONFIG,
      useValue: {
        titulo: 'Mis resultados',
        vacio: 'Aún no tienes resultados disponibles.',
        volver: '/dashboard/trabajador',
        detalleBase: '/dashboard/trabajador/resultados',
      },
    },
  ],
  templateUrl: '../../shared/resultados/resultados.html',
  styleUrl: '../../shared/resultados/consulta.scss',
})
export class TrabajadorResultados {
  readonly vm = inject(ResultadosViewModel);
}
