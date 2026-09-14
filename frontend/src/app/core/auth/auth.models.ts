/**
 * Contrato de identidad y tokens de la API. ROLE_DASHBOARDS valida la pareja rol/panel
 * recibida y genera rutas; mantenerlo alineado con application/services/auth_identity.py. La
 * contraseña no forma parte de la identidad almacenada.
 */
export const ROLE_DASHBOARDS = {
  NUEVO_TRABAJADOR: '/dashboard/nuevo-trabajador',
  TRABAJADOR: '/dashboard/trabajador',
  PSICOLOGO: '/dashboard/psicologo',
  ADMIN: '/dashboard/admin',
  SUPERADMIN: '/dashboard/superadmin',
} as const;
export type FunctionalRole = keyof typeof ROLE_DASHBOARDS;
/**
 * Identidad validada en memoria: dashboard_path viene del servidor y debe coincidir con role.
 */
export interface AuthUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: FunctionalRole;
  dashboard_path: string;
}
/**
 * Par access/refresh del login; access autoriza solicitudes y refresh permite renovarlo.
 */
export interface TokenPair {
  access: string;
  refresh: string;
}
/**
 * Respuesta de login: dashboard_path está fuera de user; AuthService la combina antes de
 * guardarla.
 */
export interface LoginResponse extends TokenPair {
  user: Omit<AuthUser, 'dashboard_path'>;
  dashboard_path: string;
}
