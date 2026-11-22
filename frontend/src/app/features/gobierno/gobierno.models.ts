export interface Politica {id:string;tipo:string;titulo:string;version:string;contenido:string;vigente_desde:string;obligatoria:boolean;activo:boolean}
export interface Evento {id:string;actor_id:string|null;fecha:string;accion:string;entidad:string;entidad_id:string|null;estado:string}
export interface Eventos {count:number;page:number;page_size:number;results:Evento[]}
