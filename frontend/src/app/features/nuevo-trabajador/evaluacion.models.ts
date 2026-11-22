export type ValorRespuesta = string | boolean | null;

export interface ResultadoEvaluacion {
  aplicacion_id: string;
  instrumento_id: string;
  nombre: string;
  version: string;
  fecha_calculo: string;
  puntaje_total: string;
  rango: string | null;
  interpretacion: string;
  tamizaje_resuelto: boolean;
  nuevo_rol: 'TRABAJADOR';
  dashboard_path: string;
  estado_asignacion_profesional: 'ASIGNADO' | 'PENDIENTE';
}

export interface PreguntaEvaluacion {
  id: string;
  texto: string;
  orden: number;
  tipo_respuesta: 'ESCALA' | 'TEXTO' | 'NUMERO' | 'BOOLEANO';
  obligatoria: boolean;
  opciones: { id: string; etiqueta: string }[];
}

export interface RespuestaEvaluacion {
  pregunta_id: string;
  opcion_id: string | null;
  valor_texto: string | null;
  valor_numerico: string | null;
  valor_booleano: boolean | null;
}

export interface EvaluacionDetalle {
  asignacion_id: string;
  instrumento_id: string;
  nombre: string;
  version: string;
  instrucciones: string;
  estado_asignacion: 'PENDIENTE' | 'EN_PROGRESO' | 'COMPLETADA' | 'CANCELADA';
  aplicacion_id: string | null;
  estado_aplicacion: 'INICIADA' | 'FINALIZADA' | 'ANULADA' | null;
  fecha_inicio: string | null;
  fecha_finalizacion: string | null;
  disponible: boolean;
  preguntas: PreguntaEvaluacion[];
  respuestas: RespuestaEvaluacion[];
}
