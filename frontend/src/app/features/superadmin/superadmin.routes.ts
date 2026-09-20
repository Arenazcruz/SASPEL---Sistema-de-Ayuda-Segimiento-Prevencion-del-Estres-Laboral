/**
 * Rutas hijas del panel: resumen, personas, fichas, clave y catálogos. Las listas por rol
 * comparten componente mediante data.filterRole; áreas/cargos mediante data.kind. Mantener
 * rutas literales antes de personas/:id y revisar los enlaces del layout al añadir páginas.
 */
import { inject } from '@angular/core';
import { CanActivateChildFn, Router, Routes } from '@angular/router';
import { AuthService } from '../../core/auth/auth.service';

/**
 * Verifica rol en memoria en cada ruta hija y devuelve true o URL del panel/login. La
 * restauración del servidor corresponde al authGuard de la ruta padre.
 */
export const superadminChildGuard: CanActivateChildFn = () => {
  const user = inject(AuthService).user();
  return user?.role === 'SUPERADMIN'
    ? true
    : inject(Router).parseUrl(user?.dashboard_path || '/login');
};
const list = () => import('./users/user-list').then((m) => m.UserList);
export const SUPERADMIN_ROUTES: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () => import('./dashboard/dashboard').then((m) => m.SuperadminDashboard),
  },
  { path: 'personas', loadComponent: list },
  {
    path: 'personas/asignaciones-profesionales',
    loadComponent: () => import('./assignments/assignments').then((m) => m.ProfessionalAssignments),
  },
  {
    path: 'personas/nuevo',
    loadComponent: () => import('./users/user-form').then((m) => m.UserForm),
  },
  ...[
    ['nuevos-trabajadores', 'NUEVO_TRABAJADOR', 'Nuevos trabajadores'],
    ['trabajadores', 'TRABAJADOR', 'Trabajadores'],
    ['psicologos', 'PSICOLOGO', 'Psicólogos'],
    ['administradores', 'ADMIN', 'Administradores'],
  ].map(([path, filterRole, title]) => ({
    path: `personas/${path}`,
    data: { filterRole, title },
    loadComponent: list,
  })),
  {
    path: 'personas/:id/editar',
    loadComponent: () => import('./users/user-form').then((m) => m.UserForm),
  },
  {
    path: 'personas/:id/password',
    loadComponent: () => import('./users/user-password').then((m) => m.UserPassword),
  },
  {
    path: 'personas/:id',
    loadComponent: () => import('./users/user-detail').then((m) => m.UserDetail),
  },
  ...['areas', 'cargos'].map((kind) => ({
    path: `institucion/${kind}`,
    data: { kind },
    loadComponent: () => import('./institution/institution').then((m) => m.InstitutionComponent),
  })),
];
