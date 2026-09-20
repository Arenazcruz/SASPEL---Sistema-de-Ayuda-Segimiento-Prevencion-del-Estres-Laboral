/** Contratos T23; las fechas llegan en ISO y los estados cerrados conservan el historial. */
import { FunctionalRole } from '../../../core/auth/auth.models';

export type AssignmentState = 'ACTIVA' | 'FINALIZADA' | 'REASIGNADA';

export interface AssignmentPerson {
  id: number;
  nombre_completo: string;
  email: string;
  codigo_empleado: string;
  role: FunctionalRole | null;
  is_active: boolean;
  habilitado_asignaciones: boolean;
}

export interface ProfessionalAssignment {
  id: number;
  trabajador: AssignmentPerson;
  psicologo: AssignmentPerson;
  fecha_asignacion: string;
  fecha_fin: string | null;
  estado: AssignmentState;
  motivo_fin: string;
}

export interface AssignmentPage<T> {
  count: number;
  page: number;
  page_size: number;
  results: T[];
}

export interface PsychologistLoad {
  psicologo: AssignmentPerson;
  trabajadores_activos: number;
}

export type AssignmentAction =
  | { kind: 'assign'; worker: AssignmentPerson }
  | { kind: 'reassign' | 'finish'; assignment: ProfessionalAssignment };
