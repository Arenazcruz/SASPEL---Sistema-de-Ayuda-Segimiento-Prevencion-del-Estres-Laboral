/**
 * Centraliza POST /api/auth/login/, GET /api/auth/me/ y POST /api/auth/refresh/ (base
 * configurable en API_URL). Mantiene identidad reactiva y tokens mediante TokenStorageService;
 * guards e interceptor dependen de este estado.
 */
import { HttpClient } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, finalize, map, Observable, of, shareReplay, tap, throwError } from 'rxjs';
import { API_URL } from './api-url';
import { AuthUser, LoginResponse, ROLE_DASHBOARDS } from './auth.models';
import { TokenStorageService } from './token-storage.service';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly storage = inject(TokenStorageService);
  private readonly api = inject(API_URL);
  private readonly identity = signal<AuthUser | null>(null);
  readonly user = this.identity.asReadonly();
  private restoring?: Observable<AuthUser | null>;
  private refreshing?: Observable<string>;
  // Impide que una respuesta tardía vuelva a abrir una sesión que ya se cerró.
  private sessionVersion = 0;

  /**
   * Recibe correo/clave y devuelve Observable<AuthUser>. Limpia primero la sesión previa; al
   * recibir respuesta válida guarda tokens e identidad. Rechaza respuestas de una sesión
   * reemplazada y propaga errores al formulario.
   */
  login(email: string, password: string): Observable<AuthUser> {
    this.clearSession();
    const version = this.sessionVersion;
    return this.http.post<LoginResponse>(`${this.api}/auth/login/`, { email, password }).pipe(
      map((response) => {
        const user = this.validatedUser({
          ...response.user,
          dashboard_path: response.dashboard_path,
        });
        if (version !== this.sessionVersion) throw new Error('La sesión cambió.');
        this.storage.save(response);
        this.identity.set(user);
        return user;
      }),
    );
  }

  /**
   * Devuelve identidad vigente consultando me, o null sin tokens/ante fallo. Comparte una
   * consulta en curso y actualiza el estado solo si sigue siendo la misma sesión; guards
   * dependen de esta protección contra respuestas tardías.
   */
  restoreSession(): Observable<AuthUser | null> {
    if (!this.storage.access && !this.storage.refresh) {
      this.identity.set(null);
      return of(null);
    }
    if (this.restoring) return this.restoring;
    const version = this.sessionVersion;
    this.restoring = this.http.get<AuthUser>(`${this.api}/auth/me/`).pipe(
      map((user) => this.validatedUser(user)),
      map((user) => (version === this.sessionVersion ? user : null)),
      tap((user) => {
        if (version === this.sessionVersion) this.identity.set(user);
      }),
      catchError(() => {
        if (version === this.sessionVersion) this.clearSession();
        return of(null);
      }),
      finalize(() => {
        if (version === this.sessionVersion) this.restoring = undefined;
      }),
      shareReplay({ bufferSize: 1, refCount: false }),
    );
    return this.restoring;
  }

  /**
   * Devuelve un observable compartido con nuevo access y lo guarda. Requiere refresh local;
   * rechaza resultados tras logout. Conserva la comprobación de sessionVersion y shareReplay
   * para solicitudes concurrentes.
   */
  refreshAccess(): Observable<string> {
    if (this.refreshing) return this.refreshing;
    const refresh = this.storage.refresh;
    if (!refresh) return throwError(() => new Error('No hay sesión para renovar.'));
    const version = this.sessionVersion;
    this.refreshing = this.http
      .post<{ access: string }>(`${this.api}/auth/refresh/`, { refresh })
      .pipe(
        map((response) => response.access),
        tap((access) => {
          if (version !== this.sessionVersion) throw new Error('La sesión ya se cerró.');
          this.storage.updateAccess(access);
        }),
        finalize(() => {
          if (version === this.sessionVersion) this.refreshing = undefined;
        }),
        shareReplay({ bufferSize: 1, refCount: false }),
      );
    return this.refreshing;
  }

  /**
   * Limpia tokens e identidad y navega a /login. No llama al backend ni invalida JWT emitidos;
   * si se implementa revocación habrá que conectar aquí esa operación.
   */
  logout(): void {
    this.clearSession();
    void this.router.navigateByUrl('/login');
  }

  /**
   * Invalida respuestas pendientes incrementando sessionVersion, borra tokens/identidad y
   * referencias de consultas. No navega; lo utilizan login, logout y restauración fallida.
   */
  private clearSession(): void {
    this.sessionVersion++;
    this.storage.clear();
    this.identity.set(null);
    this.restoring = undefined;
    this.refreshing = undefined;
  }

  /**
   * Devuelve la identidad solo si rol y dashboard_path coinciden con ROLE_DASHBOARDS; si no,
   * lanza error. Actualizar ambos mapas backend/frontend al incorporar roles.
   */
  private validatedUser(user: AuthUser): AuthUser {
    if (
      !Object.hasOwn(ROLE_DASHBOARDS, user.role) ||
      ROLE_DASHBOARDS[user.role] !== user.dashboard_path
    ) {
      throw new Error('El panel recibido no es válido.');
    }
    return user;
  }
}
