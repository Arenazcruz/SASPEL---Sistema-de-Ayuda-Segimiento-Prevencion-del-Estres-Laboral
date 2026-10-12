import { inject } from '@angular/core';
import { CanActivateChildFn, Router } from '@angular/router';
import { map } from 'rxjs';
import { AuthService } from './auth.service';
import { sessionDestination } from './auth.models';

/** Consulta me en cada navegación; el servidor decide el paso, incluso tras publicar otra versión. */
export const primerAccesoGuard: CanActivateChildFn = (_route, state) => {
  const router = inject(Router);
  return inject(AuthService)
    .restoreSession()
    .pipe(
      map((user) => {
        if (!user) return router.parseUrl('/login');
        const destination = sessionDestination(user);
        const current = state.url.split(/[?#]/)[0];
        const onboarding = current.startsWith('/primer-acceso');
        if (user.primer_acceso && !user.primer_acceso.completo) {
          return current === destination ? true : router.parseUrl(destination);
        }
        return onboarding ? router.parseUrl(user.dashboard_path) : true;
      }),
    );
};
