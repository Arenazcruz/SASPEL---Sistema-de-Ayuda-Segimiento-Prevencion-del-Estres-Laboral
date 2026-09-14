/**
 * Ficha de persona: muestra datos y acciones del UserDetailViewModel. Detalle visual en user-
 * detail.html; cambios de rol y estado se envían desde el ViewModel mediante
 * SuperadminService.
 */
import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { RoleBadge } from '../shared/role-badge';
import { UserDetailViewModel } from './user-detail.viewmodel';

@Component({
  selector: 'app-user-detail',
  imports: [DatePipe, RouterLink, RoleBadge],
  providers: [UserDetailViewModel],
  templateUrl: './user-detail.html',
})
export class UserDetail {
  readonly vm = inject(UserDetailViewModel);
}
