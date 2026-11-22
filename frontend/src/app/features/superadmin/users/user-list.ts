/**
 * Pantalla única de usuarios. UserListViewModel carga
 * personas y catálogos; user-list.html presenta búsqueda, paginación y activación.
 */
import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink, RouterOutlet } from '@angular/router';
import { RoleBadge } from '../shared/role-badge';
import { UserListViewModel } from './user-list.viewmodel';

@Component({
  selector: 'app-user-list',
  imports: [DatePipe, ReactiveFormsModule, RouterLink, RouterOutlet, RoleBadge],
  providers: [UserListViewModel],
  templateUrl: './user-list.html',
  styleUrl: './user-list.scss',
})
export class UserList {
  readonly vm = inject(UserListViewModel);
  readonly base = '/dashboard/superadmin/personas';
  private readonly router = inject(Router);
  private modalContent: { vm?: { saving?: () => boolean; busy?: () => boolean } } | null = null;
  private returnFocus: HTMLElement | null = null;

  openDialog(dialog: HTMLDialogElement, content: unknown) {
    this.modalContent = content as typeof this.modalContent;
    if (!dialog.open) {
      this.returnFocus = document.activeElement as HTMLElement;
      dialog.showModal();
    }
  }

  closeDialog(event?: Event) {
    event?.preventDefault();
    if (this.modalContent?.vm?.saving?.() || this.modalContent?.vm?.busy?.()) return;
    void this.router.navigate([this.base], { queryParamsHandling: 'preserve' });
  }

  onDeactivate(dialog: HTMLDialogElement) {
    // Espera a que termine la navegación: Ver → Editar conserva el mismo modal abierto.
    queueMicrotask(() => {
      if (!this.router.url.split('?')[0].endsWith('/personas')) return;
      dialog.close();
      this.returnFocus?.focus();
      this.vm.reload();
    });
  }
}
