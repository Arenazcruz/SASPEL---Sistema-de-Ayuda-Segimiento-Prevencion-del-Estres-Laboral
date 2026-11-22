export interface TipoFactor {id:string;nombre:string;descripcion:string;activo:boolean;}
export interface DatosFactor {tipo_id:string;nivel:string;descripcion:string;}
export interface RegistroFactor extends DatosFactor {id:string;tipo:string;fecha:string;}
export interface HistorialFactores {trabajador:string;registros:RegistroFactor[];}
