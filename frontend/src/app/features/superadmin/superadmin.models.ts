/**
 * Tipos de las respuestas administrativas y etiquetas de roles. Reflejan DTO del backend: las
 * fechas viajan como strings y persona puede carecer de perfil o rol. CREATION_ROLES excluye
 * TRABAJADOR; sincronizar con el caso CreateUser al cambiar altas.
 */
import { FunctionalRole } from '../../core/auth/auth.models';

export const ROLE_LABELS: Record<FunctionalRole, string> = {
  NUEVO_TRABAJADOR: 'Nuevo trabajador',
  TRABAJADOR: 'Trabajador',
  PSICOLOGO: 'Psicólogo',
  ADMIN: 'Administrador',
  SUPERADMIN: 'Superadmin',
};
export const ROLES = Object.entries(ROLE_LABELS) as [FunctionalRole, string][];
export const CREATION_ROLES = ROLES.filter(([role]) => role !== 'TRABAJADOR');
export type InstitutionKind = 'areas' | 'cargos';
/**
 * Catálogo anidado o de listado; activo=false permite representar vínculos históricos.
 */
export interface Institution {
  id: number;
  nombre: string;
  descripcion: string;
  activo: boolean;
}
/**
 * Ficha de User y perfil. tiene_perfil=false identifica cuenta incompleta;
 * habilitado_asignaciones no equivale a is_active y tamizaje_resuelto no cambia el rol desde
 * esta interfaz.
 */
export interface Person {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  nombre_completo: string;
  role: FunctionalRole | null;
  is_active: boolean;
  fecha_registro: string;
  last_login: string | null;
  codigo_empleado: string;
  apellido_materno: string;
  nombre_preferido: string;
  fecha_nacimiento: string | null;
  sexo: string;
  telefono: string;
  area: Institution | null;
  cargo: Institution | null;
  tamizaje_resuelto: boolean;
  habilitado_asignaciones: boolean;
  tiene_perfil: boolean;
}
/**
 * count es el total filtrado; results contiene solo la página indicada por page/page_size.
 */
export interface UserPage {
  count: number;
  page: number;
  page_size: number;
  results: Person[];
}
/**
 * Estadísticas y recientes del backend para las tarjetas; no se derivan del listado paginado.
 */
export interface Summary {
  users_total: number;
  new_workers: number;
  workers: number;
  psychologists: number;
  admins: number;
  superadmins: number;
  active_users: number;
  inactive_users: number;
  recent_users: Person[];
}
