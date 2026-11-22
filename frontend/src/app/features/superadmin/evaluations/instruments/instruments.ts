import { DatePipe } from '@angular/common';
import { afterRenderEffect, Component, ElementRef, inject, viewChild } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { InstrumentsViewModel } from './instruments.viewmodel';

@Component({
  selector: 'app-instruments',
  imports: [DatePipe, ReactiveFormsModule],
  providers: [InstrumentsViewModel],
  templateUrl: './instruments.html',
  styleUrl: './instruments.scss',
})
export class Instruments {
  readonly vm = inject(InstrumentsViewModel);
  private readonly dialog = viewChild<ElementRef<HTMLDialogElement>>('instrumentDialog');
  private returnFocus: HTMLElement | null = null;

  constructor() {
    afterRenderEffect(() => {
      const mode = this.vm.mode();
      const dialog = this.dialog()?.nativeElement;
      if (!dialog) return;
      if (mode && !dialog.open) {
        this.returnFocus = document.activeElement as HTMLElement;
        dialog.showModal();
      } else if (!mode && dialog.open) {
        dialog.close();
        this.returnFocus?.focus();
      }
    });
  }
  close(event?: Event) {
    event?.preventDefault();
    this.vm.close();
  }
}
