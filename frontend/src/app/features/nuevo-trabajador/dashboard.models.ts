export interface EvaluacionInicial {
  estado: 'SIN_ASIGNAR' | 'PENDIENTE' | 'EN_PROGRESO' | 'COMPLETADA';
  asignacion_id: string | null;
  instrumento_id: string | null;
  nombre: string | null;
  version: string | null;
  fecha_asignacion: string | null;
  fecha_limite: string | null;
  puede_iniciar: boolean;
}

export interface DashboardResumen {
  evaluacion_inicial: EvaluacionInicial;
}
