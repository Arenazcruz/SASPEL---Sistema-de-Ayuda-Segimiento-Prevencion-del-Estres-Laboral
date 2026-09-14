/**
 * Controla acceso a rutas privadas y evita mostrar login a quien tiene sesión. Ambos guards
 * consultan restoreSession; roleGuard se ejecuta después para comprobar el panel concreto.
 */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map } from 'rxjs';
import { AuthService } from './auth.service';

/**
 * Devuelve observable de permiso o URL /login después de comprobar la sesión en el servidor.
 */
export const authGuard: CanActivateFn = () => {
  const router = inject(Router);
  return inject(AuthService)
    .restoreSession()
    .pipe(map((user) => (user ? true : router.createUrlTree(['/login']))));
};

// Una persona que ya tiene sesión no necesita volver a introducir su contraseña.
/**
 * Permite login sin identidad o devuelve la URL del panel propio si la sesión pudo
 * restaurarse.
 */
export const guestGuard: CanActivateFn = () => {
  const router = inject(Router);
  return inject(AuthService)
    .restoreSession()
    .pipe(map((user) => (user ? router.parseUrl(user.dashboard_path) : true)));
};
