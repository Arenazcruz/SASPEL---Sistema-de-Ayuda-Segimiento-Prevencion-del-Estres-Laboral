export interface AsignacionInstrumento {id:string;instrumento_id:string;nombre:string;version:string;estado:string;fecha_asignacion:string;fecha_limite:string|null;activo:boolean}
export interface CatalogoInstrumento {id:string;nombre:string;version:string}
export interface Asignaciones {asignaciones:AsignacionInstrumento[];instrumentos?:CatalogoInstrumento[]}
