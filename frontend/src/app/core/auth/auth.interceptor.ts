/**
 * Añade Bearer solo a peticiones dentro del origen y prefijo de API_URL, excluyendo login y
 * refresh. Ante 401 renueva access (o reutiliza uno recién renovado) y reintenta una vez. Si
 * renovación o reintento fallan, cierra la sesión aún vigente; otras respuestas y sesiones
 * reemplazadas propagan el error. Cambiar endpoints de sesión exige actualizar las exclusiones
 * para evitar ciclos.
 */
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, of, switchMap, throwError } from 'rxjs';
import { API_URL } from './api-url';
import { AuthService } from './auth.service';
import { TokenStorageService } from './token-storage.service';

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const base = new URL(inject(API_URL) + '/', window.location.origin);
  const target = new URL(request.url, window.location.origin);
  if (target.origin !== base.origin || !target.pathname.startsWith(base.pathname))
    return next(request);
  const endpoint = target.pathname.slice(base.pathname.length);
  if (endpoint === 'auth/login/' || endpoint === 'auth/refresh/') return next(request);
  const storage = inject(TokenStorageService);
  const auth = inject(AuthService);
  const sentToken = storage.access;
  const sessionRefresh = storage.refresh;
  const authorized = sentToken
    ? request.clone({ setHeaders: { Authorization: `Bearer ${sentToken}` } })
    : request;
  return next(authorized).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status !== 401) return throwError(() => error);
      if (storage.refresh !== sessionRefresh) return throwError(() => error);
      // Otra solicitud puede haber renovado ya el token mientras esta esperaba.
      const renewed =
        storage.access && storage.access !== sentToken ? of(storage.access) : auth.refreshAccess();
      return renewed.pipe(
        switchMap((access) =>
          next(request.clone({ setHeaders: { Authorization: `Bearer ${access}` } })),
        ),
        catchError((refreshError) => {
          if (storage.refresh === sessionRefresh) auth.logout();
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};
