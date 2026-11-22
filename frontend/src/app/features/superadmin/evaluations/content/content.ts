import { DatePipe } from '@angular/common';
import { afterRenderEffect, Component, ElementRef, inject, viewChild } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { InstrumentContentViewModel } from './content.viewmodel';

@Component({
  selector: 'app-instrument-content',
  imports: [DatePipe, ReactiveFormsModule],
  providers: [InstrumentContentViewModel],
  templateUrl: './content.html',
  styleUrls: ['../instruments/instruments.scss', './content.scss'],
})
export class InstrumentContent {
  readonly vm = inject(InstrumentContentViewModel);
  private readonly dialog = viewChild<ElementRef<HTMLDialogElement>>('contentDialog');
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
