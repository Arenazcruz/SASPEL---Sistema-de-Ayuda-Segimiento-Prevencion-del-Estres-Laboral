/**
 * Centraliza HTTP bajo /api/superadmin (API_URL configurable). Devuelve observables que los
 * ViewModels suscriben para cargar o guardar; errores se presentan con apiError. Al cambiar
 * endpoints revisar superadmin_urls.py y POSTMAN_PRUEBAS.md.
 */
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { API_URL } from '../../core/auth/api-url';
import { Institution, InstitutionKind, Person, Summary, UserPage } from './superadmin.models';

@Injectable({ providedIn: 'root' })
export class SuperadminService {
  private readonly http = inject(HttpClient);
  private readonly base = `${inject(API_URL)}/superadmin`;
  /**
   * GET dashboard/summary/: devuelve Observable<Summary> con totales y recientes.
   */
  summary() {
    return this.http.get<Summary>(`${this.base}/dashboard/summary/`);
  }
  /**
   * GET users/: envía filtros no vacíos como query params y devuelve Observable<UserPage>. La
   * búsqueda, orden y paginación se resuelven en el servidor.
   */
  users(filters: Record<string, string | number>) {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(filters))
      if (value !== '') params = params.set(key, value);
    return this.http.get<UserPage>(`${this.base}/users/`, { params });
  }
  /**
   * GET users/{id}/: devuelve Observable<Person>; un ID inexistente produce error HTTP.
   */
  user(id: number) {
    return this.http.get<Person>(`${this.base}/users/${id}/`);
  }
  /**
   * POST users/: envía alta personal, rol y clave confirmada; devuelve Observable<Person>
   * creada.
   */
  create(data: object) {
    return this.http.post<Person>(`${this.base}/users/`, data);
  }
  /**
   * PATCH users/{id}/: envía cambios personales parciales y devuelve Observable<Person>. No
   * usar para rol, estado o clave.
   */
  update(id: number, data: object) {
    return this.http.patch<Person>(`${this.base}/users/${id}/`, data);
  }
  /**
   * POST users/{id}/activate/ o deactivate/ según active; devuelve persona actualizada y
   * conserva el registro.
   */
  active(id: number, active: boolean) {
    return this.http.post<Person>(
      `${this.base}/users/${id}/${active ? 'activate' : 'deactivate'}/`,
      {},
    );
  }
  /**
   * POST users/{id}/role/: devuelve persona con nuevo rol; el backend protege transiciones y
   * último Superadmin.
   */
  role(id: number, role: string) {
    return this.http.post<Person>(`${this.base}/users/${id}/role/`, { role });
  }
  /**
   * POST users/{id}/reset-password/: envía clave y confirmación y devuelve mensaje detail.
   */
  password(id: number, data: object) {
    return this.http.post<{ detail: string }>(`${this.base}/users/${id}/reset-password/`, data);
  }
  /**
   * GET {kind}/, areas o cargos; activeOnly añade active=true. Devuelve observable del
   * catálogo completo o activo.
   */
  institution(kind: InstitutionKind, activeOnly = false) {
    return this.http.get<Institution[]>(`${this.base}/${kind}/`, {
      params: activeOnly ? { active: 'true' } : {},
    });
  }
  /**
   * POST {kind}/ si no hay ID o PATCH {kind}/{id}/ al editar; recibe nombre/descripcion y
   * devuelve catálogo guardado.
   */
  saveInstitution(kind: InstitutionKind, id: number | null, data: object) {
    return id
      ? this.http.patch<Institution>(`${this.base}/${kind}/${id}/`, data)
      : this.http.post<Institution>(`${this.base}/${kind}/`, data);
  }
  /**
   * POST {kind}/{id}/activate/ o deactivate/; devuelve registro actualizado sin borrar
   * vínculos.
   */
  institutionActive(kind: InstitutionKind, id: number, active: boolean) {
    return this.http.post<Institution>(
      `${this.base}/${kind}/${id}/${active ? 'activate' : 'deactivate'}/`,
      {},
    );
  }
}

/**
 * Convierte HttpErrorResponse a texto para los ViewModels; distingue conexión, acceso,
 * ausencia y servidor. Para 400 combina mensajes por campo; no modifica la respuesta original.
 */
export function apiError(error: HttpErrorResponse): string {
  if (error.status === 0) return 'No pudimos conectar con SASPEL. Inténtalo nuevamente.';
  if (error.status === 403) return 'No tienes acceso a esta función. Revisa tu sesión.';
  if (error.status === 404) return 'El registro solicitado no existe.';
  if (error.status >= 500) return 'No se pudo completar la operación. Inténtalo nuevamente.';
  const body = error.error;
  if (body && typeof body === 'object') return Object.values(body).flat().join(' ');
  return 'No se pudo completar la operación.';
}
