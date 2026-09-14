/**
 * Pantalla de listado reutilizada por filtros de rol del sidebar. UserListViewModel carga
 * personas y catálogos; user-list.html presenta búsqueda, paginación y activación.
 */
import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { RoleBadge } from '../shared/role-badge';
import { UserListViewModel } from './user-list.viewmodel';

@Component({
  selector: 'app-user-list',
  imports: [DatePipe, ReactiveFormsModule, RouterLink, RoleBadge],
  providers: [UserListViewModel],
  templateUrl: './user-list.html',
})
export class UserList {
  readonly vm = inject(UserListViewModel);
  readonly base = '/dashboard/superadmin/personas';
}
