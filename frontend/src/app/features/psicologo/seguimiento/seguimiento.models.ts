export interface DatosSeguimiento {
 motivo:string;categoria:string;observacion:string;estado:string;evolucion:string;plan_accion:string;proxima_revision:string|null;
}
export interface Seguimiento extends DatosSeguimiento {id:string;fecha:string;profesional:string;profesional_id:string;trabajador_id:string;}
export interface HistorialSeguimiento {trabajador:string;registros:Seguimiento[];}
