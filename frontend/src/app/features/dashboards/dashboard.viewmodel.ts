/**
 * Selecciona título y descripción por rol y muestra nombre o correo desde AuthService. PANELS
 * mantiene también una entrada SUPERADMIN, aunque su ruta principal usa el módulo
 * administrativo propio. Cambiar aquí textos de los paneles generales; las rutas están en
 * app.routes.ts.
 */
import { computed, inject, Injectable } from '@angular/core';
import { AuthService } from '../../core/auth/auth.service';
import { FunctionalRole } from '../../core/auth/auth.models';

const PANELS: Record<FunctionalRole, { title: string; label: string; description: string }> = {
  NUEVO_TRABAJADOR: {
    title: 'Panel de bienvenida del nuevo trabajador',
    label: 'Nuevo trabajador',
    description: 'Antes de acceder al sistema completo deberás completar tu proceso inicial.',
  },
  TRABAJADOR: {
    title: 'Panel del trabajador',
    label: 'Trabajador',
    description:
      'Desde aquí se accederá posteriormente a evaluaciones, estado de ánimo, citas y seguimiento.',
  },
  PSICOLOGO: {
    title: 'Panel del psicólogo',
    label: 'Psicólogo',
    description:
      'Desde aquí podrás acceder más adelante a las herramientas de atención y acompañamiento profesional.',
  },
  ADMIN: {
    title: 'Panel administrativo',
    label: 'Administrador',
    description:
      'Las herramientas de administración institucional se incorporarán en las próximas etapas.',
  },
  SUPERADMIN: {
    title: 'Panel de superadministración',
    label: 'Superadministrador',
    description:
      'Las herramientas de gestión general de SASPEL se incorporarán en las próximas etapas.',
  },
};

@Injectable()
export class DashboardViewModel {
  private readonly auth = inject(AuthService);
  readonly user = this.auth.user;
  readonly panel = computed(() => (this.user() ? PANELS[this.user()!.role] : null));
  readonly displayName = computed(() => {
    const user = this.user();
    return user ? [user.first_name, user.last_name].filter(Boolean).join(' ') || user.email : '';
  });
  logout(): void {
    this.auth.logout();
  }
}
