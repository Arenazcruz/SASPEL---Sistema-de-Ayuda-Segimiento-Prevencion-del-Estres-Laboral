/**
 * Provee la base HTTP de environment tal como está configurada, sin barra final. AuthService,
 * SuperadminService e interceptor deben compartir esta base para que los JWT lleguen
 * únicamente a SASPEL.
 */
import { InjectionToken } from '@angular/core';
import { environment } from '../../../environments/environment';
export const API_URL = new InjectionToken<string>('SASPEL_API_URL', {
  providedIn: 'root',
  factory: () => environment.apiUrl,
});
