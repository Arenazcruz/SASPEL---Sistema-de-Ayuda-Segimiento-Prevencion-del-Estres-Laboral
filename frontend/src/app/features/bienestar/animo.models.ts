export interface DatosAnimo {estado:string;intensidad:string;comentario:string;}
export interface RegistroAnimo extends DatosAnimo {id:string;fecha:string;}
export interface HistorialAnimo {trabajador:string;registros:RegistroAnimo[];}
