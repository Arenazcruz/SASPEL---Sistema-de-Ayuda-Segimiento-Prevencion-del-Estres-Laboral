/**
 * Formulario de alta/edición personal. UserFormViewModel distingue operación por ID de ruta y
 * carga catálogos; editar la plantilla en user-form.html y las reglas de envío en el
 * ViewModel.
 */
import { Component, inject } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { UserFormViewModel } from './user-form.viewmodel';

@Component({
  selector: 'app-user-form',
  imports: [ReactiveFormsModule, RouterLink],
  providers: [UserFormViewModel],
  templateUrl: './user-form.html',
})
export class UserForm {
  readonly vm = inject(UserFormViewModel);
}
