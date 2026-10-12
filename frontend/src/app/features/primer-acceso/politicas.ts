import { Component, inject } from '@angular/core';
import { Brand } from '../../shared/brand/brand';
import { PrimerAccesoPoliticasViewModel } from './politicas.viewmodel';

@Component({
  selector: 'app-primer-acceso-politicas',
  imports: [Brand],
  providers: [PrimerAccesoPoliticasViewModel],
  templateUrl: './politicas.html',
  styleUrl: './primer-acceso.scss',
})
export class PrimerAccesoPoliticas {
  readonly vm = inject(PrimerAccesoPoliticasViewModel);
}
