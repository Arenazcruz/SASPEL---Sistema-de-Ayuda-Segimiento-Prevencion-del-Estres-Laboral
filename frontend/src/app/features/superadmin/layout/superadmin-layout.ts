/**
 * Marco del panel con sidebar, cabecera e identidad de AuthService. Controla expansión de
 * grupos, modo compacto y menú móvil; enlaces en superadmin-layout.html y estilos en
 * superadmin-layout.scss. El contenido se monta en RouterOutlet.
 */
import { Component, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../../../core/auth/auth.service';
import { Brand } from '../../../shared/brand/brand';

// El menú publica únicamente las funciones disponibles en SA-01.
export const PERSON_LINKS = [
  ['Usuarios', 'personas'],
  ['Nuevos trabajadores', 'personas/nuevos-trabajadores'],
  ['Trabajadores', 'personas/trabajadores'],
  ['Psicólogos', 'personas/psicologos'],
  ['Administradores', 'personas/administradores'],
];

@Component({
  selector: 'app-superadmin-layout',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, Brand],
  templateUrl: './superadmin-layout.html',
  styleUrl: './superadmin-layout.scss',
})
export class SuperadminLayout {
  readonly auth = inject(AuthService);
  readonly collapsed = signal(false);
  readonly mobileOpen = signal(false);
  readonly peopleOpen = signal(true);
  readonly institutionOpen = signal(true);
  readonly links = PERSON_LINKS;
  readonly base = '/dashboard/superadmin';
}
