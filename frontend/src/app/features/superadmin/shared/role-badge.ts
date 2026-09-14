/**
 * Etiqueta visual de rol usando ROLE_LABELS; recibe rol funcional o null. Cambiar textos en
 * superadmin.models.ts y colores en los estilos administrativos.
 */
import { Component, input } from '@angular/core';
import { FunctionalRole } from '../../../core/auth/auth.models';
import { ROLE_LABELS } from '../superadmin.models';

@Component({
  selector: 'app-role-badge',
  template: `<span class="sa-badge" [attr.data-role]="role()">{{
    role() ? labels[role()!] : 'Sin rol'
  }}</span>`,
})
export class RoleBadge {
  readonly role = input<FunctionalRole | null>(null);
  readonly labels = ROLE_LABELS;
}
