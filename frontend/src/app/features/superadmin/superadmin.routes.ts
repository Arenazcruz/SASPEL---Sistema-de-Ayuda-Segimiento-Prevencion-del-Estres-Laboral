/**
 * Un listado de usuarios con filtros por query params y formularios/fichas en su modal.
 * Las rutas antiguas por categoría redirigen al mismo listado.
 */
import { inject } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivateChildFn, Router, Routes } from '@angular/router';
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
    path: 'evaluaciones/instrumentos',
    loadComponent: () => import('./evaluations/instruments/instruments').then((m) => m.Instruments),
  },
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () => import('./dashboard/dashboard').then((m) => m.SuperadminDashboard),
  },
  {
    path: 'personas/asignaciones-profesionales',
    loadComponent: () => import('./assignments/assignments').then((m) => m.ProfessionalAssignments),
  },
  ...[
    ['nuevos-trabajadores', 'NUEVO_TRABAJADOR', 'Nuevos trabajadores'],
    ['trabajadores', 'TRABAJADOR', 'Trabajadores'],
    ['psicologos', 'PSICOLOGO', 'Psicólogos'],
    ['administradores', 'ADMINISTRADORES', 'Administradores'],
  ].map(([path, filterRole]) => ({
    path: `personas/${path}`,
    pathMatch: 'full' as const,
    redirectTo: ({ queryParams }: Pick<ActivatedRouteSnapshot, 'queryParams'>) =>
      inject(Router).createUrlTree(['/dashboard/superadmin/personas'], {
        queryParams: { ...queryParams, role: filterRole, page: 1 },
      }),
  })),
  {
    path: 'personas',
    loadComponent: list,
    children: [
      { path: 'nuevo', loadComponent: () => import('./users/user-form').then((m) => m.UserForm) },
      {
        path: ':id/editar',
        loadComponent: () => import('./users/user-form').then((m) => m.UserForm),
      },
      {
        path: ':id/password',
        loadComponent: () => import('./users/user-password').then((m) => m.UserPassword),
      },
      { path: ':id', loadComponent: () => import('./users/user-detail').then((m) => m.UserDetail) },
    ],
  },
  ...['areas', 'cargos'].map((kind) => ({
    path: `institucion/${kind}`,
    data: { kind },
    loadComponent: () => import('./institution/institution').then((m) => m.InstitutionComponent),
  })),
];
