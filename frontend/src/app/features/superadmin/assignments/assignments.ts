/** Vista de T23; la coordinación y HTTP residen en ViewModel y servicio. */
import { DatePipe } from '@angular/common';
import { afterNextRender, Component, ElementRef, inject, Injector } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { AssignmentAction } from './assignments.models';
import { AssignmentsViewModel } from './assignments.viewmodel';

@Component({
  selector: 'app-professional-assignments',
  imports: [DatePipe, ReactiveFormsModule],
  providers: [AssignmentsViewModel],
  templateUrl: './assignments.html',
  styleUrl: './assignments.scss',
})
export class ProfessionalAssignments {
  readonly vm = inject(AssignmentsViewModel);
  private readonly element: ElementRef<HTMLElement> = inject(ElementRef);
  private readonly injector = inject(Injector);

  open(action: AssignmentAction) {
    this.vm.open(action);
    // Lleva el foco al formulario recién renderizado, también desde la tabla inferior.
    afterNextRender(
      () =>
        this.element.nativeElement.querySelector<HTMLElement>('#assignment-form-title')?.focus(),
      { injector: this.injector },
    );
  }
}
