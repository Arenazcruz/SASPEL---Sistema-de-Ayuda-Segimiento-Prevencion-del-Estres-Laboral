import { Component, inject } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { Brand } from '../../shared/brand/brand';
import { PrimerAccesoPasswordViewModel } from './password.viewmodel';

@Component({
  selector: 'app-primer-acceso-password',
  imports: [ReactiveFormsModule, Brand],
  providers: [PrimerAccesoPasswordViewModel],
  templateUrl: './password.html',
  styleUrl: './primer-acceso.scss',
})
export class PrimerAccesoPassword {
  readonly vm = inject(PrimerAccesoPasswordViewModel);
}
