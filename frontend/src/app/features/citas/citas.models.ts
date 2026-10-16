export interface Cita {id:string; trabajador_id:string; psicologo_id:string; trabajador:string; psicologo:string; fecha_inicio:string; fecha_fin:string; motivo:string; prioridad:string; estado:string; motivo_cierre:string; cita_origen_id:string|null;}
export interface Bloque {id:string;dia_semana:number;hora_inicio:string;hora_fin:string;}
export interface ContextoCita {psicologo:string|null;disponibilidad:Bloque[];}

export interface NotaCita {id:string;cita_id:string;profesional_id:string;profesional:string;observacion:string;fecha:string;}
