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
        path: 'nuevo-trabajador/evaluacion/:asignacionId',
        data: { role: 'NUEVO_TRABAJADOR' },
        canActivate: [roleGuard],
        loadComponent: () =>
          import('./features/nuevo-trabajador/evaluacion').then(
            (m) => m.EvaluacionInicialComponent,
          ),
        title: 'Evaluación inicial · SASPEL',
      },
      {
        path: 'nuevo-trabajador',
        data: { role: 'NUEVO_TRABAJADOR' },
        canActivate: [roleGuard],
        loadComponent: () =>
          import('./features/nuevo-trabajador/dashboard').then((m) => m.NuevoTrabajadorDashboard),
        title: 'Mi espacio · SASPEL',
      },
      {
        path: 'trabajador/resultados',
        data: { role: 'TRABAJADOR' },
        canActivate: [roleGuard],
        loadComponent: () =>
          import('./features/trabajador/resultados').then((m) => m.TrabajadorResultados),
        title: 'Mis resultados · SASPEL',
      },
      {
        path: 'trabajador/resultados/:resultadoId',
        data: { role: 'TRABAJADOR' },
        canActivate: [roleGuard],
        loadComponent: () =>
          import('./features/trabajador/resultados').then((m) => m.TrabajadorResultados),
        title: 'Detalle del resultado · SASPEL',
      },
      {
        path: 'psicologo',
        data: { role: 'PSICOLOGO' },
        canActivate: [roleGuard],
        loadComponent: () =>
          import('./features/psicologo/dashboard').then((m) => m.PsicologoDashboard),
        title: 'Mi espacio profesional · SASPEL',
      },
      {
        path: 'psicologo/trabajadores',
        data: { role: 'PSICOLOGO' },
        canActivate: [roleGuard],
        loadComponent: () =>
          import('./features/psicologo/trabajadores').then((m) => m.PsicologoTrabajadores),
        title: 'Mis trabajadores · SASPEL',
      },
      {
        path: 'psicologo/trabajadores/:trabajadorId/resultados',
        data: { role: 'PSICOLOGO' },
        canActivate: [roleGuard],
        loadComponent: () =>
          import('./features/psicologo/resultados').then((m) => m.PsicologoResultados),
        title: 'Resultados del trabajador · SASPEL',
      },
      {
        path: 'psicologo/resultados/:resultadoId',
        data: { role: 'PSICOLOGO' },
        canActivate: [roleGuard],
        loadComponent: () =>
          import('./features/psicologo/resultados').then((m) => m.PsicologoResultados),
        title: 'Detalle del resultado · SASPEL',
      },
      ...['TRABAJADOR', 'PSICOLOGO'].map(role => ({
        path: role.toLowerCase()+'/citas', data: {role}, canActivate: [roleGuard],
        loadComponent: () => import('./features/citas/citas').then(m=>m.Citas), title: 'Mis citas · SASPEL',
      })),
      ...Object.entries(ROLE_DASHBOARDS)
        .filter(([role]) => !['SUPERADMIN', 'NUEVO_TRABAJADOR', 'PSICOLOGO'].includes(role))
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
