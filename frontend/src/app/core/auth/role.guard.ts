/**
 * Compara el rol restaurado con route.data.role. Devuelve true, URL de login si falta
 * identidad o URL del panel propio si intenta otro. No consulta HTTP; depende del authGuard
 * previo y del mapa validado por AuthService.
 */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

export const roleGuard: CanActivateFn = (route) => {
  const user = inject(AuthService).user();
  const router = inject(Router);
  if (!user) return router.createUrlTree(['/login']);
  return user.role === route.data['role'] ? true : router.parseUrl(user.dashboard_path);
};
