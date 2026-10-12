/**
 * Mapa de navegación público y privado. authGuard restaura identidad antes de roleGuard;
 * Superadmin carga sus rutas hijas y Nuevo Trabajador su panel propio. Al cambiar paneles
 * revisar ROLE_DASHBOARDS, backend auth_identity y enlaces del sidebar.
 */
import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './core/auth/auth.guard';
import { roleGuard } from './core/auth/role.guard';
import { ROLE_DASHBOARDS } from './core/auth/auth.models';
import { superadminChildGuard } from './features/superadmin/superadmin.routes';
import { primerAccesoGuard } from './core/auth/primer-acceso.guard';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () => import('./features/welcome/welcome').then((m) => m.Welcome),
    title: 'SASPEL · Bienestar que nos une',
  },
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () => import('./features/auth/login/login').then((m) => m.LoginComponent),
    title: 'Iniciar sesión · SASPEL',
  },
  {
    path: 'primer-acceso',
    canActivate: [authGuard],
    canActivateChild: [primerAccesoGuard],
    children: [
      {
        path: 'password',
        loadComponent: () =>
          import('./features/primer-acceso/password').then((m) => m.PrimerAccesoPassword),
        title: 'Cambiar contraseña · SASPEL',
      },
      {
        path: 'politicas',
        loadComponent: () =>
          import('./features/primer-acceso/politicas').then((m) => m.PrimerAccesoPoliticas),
        title: 'Políticas institucionales · SASPEL',
      },
      { path: '**', redirectTo: 'password' },
    ],
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    canActivateChild: [primerAccesoGuard],
    runGuardsAndResolvers: 'always',
    children: [
      {
        path: 'superadmin',
        data: { role: 'SUPERADMIN' },
        canActivate: [roleGuard],
        canActivateChild: [superadminChildGuard],
        loadComponent: () =>
          import('./features/superadmin/layout/superadmin-layout').then((m) => m.SuperadminLayout),
        loadChildren: () =>
          import('./features/superadmin/superadmin.routes').then((m) => m.SUPERADMIN_ROUTES),
        title: 'Superadmin · SASPEL',
      },
      {
        path: 'nuevo-trabajador',
        data: { role: 'NUEVO_TRABAJADOR' },
        canActivate: [roleGuard],
        loadComponent: () =>
          import('./features/nuevo-trabajador/dashboard').then((m) => m.NuevoTrabajadorDashboard),
        title: 'Mi espacio · SASPEL',
      },
      ...Object.entries(ROLE_DASHBOARDS)
        .filter(([role]) => role !== 'SUPERADMIN' && role !== 'NUEVO_TRABAJADOR')
        .map(([role, path]) => ({
          path: path.split('/').at(-1)!,
          data: { role },
          canActivate: [roleGuard],
          loadComponent: () => import('./features/dashboards/dashboard').then((m) => m.Dashboard),
          title: 'Mi panel · SASPEL',
        })),
      {
        path: '**',
        canActivate: [roleGuard],
        loadComponent: () => import('./features/dashboards/dashboard').then((m) => m.Dashboard),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
