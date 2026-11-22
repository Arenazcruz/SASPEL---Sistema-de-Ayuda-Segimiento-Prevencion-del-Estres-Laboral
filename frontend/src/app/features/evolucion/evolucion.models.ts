export interface PuntoEvolucion {resultado_id:string;fecha:string;puntaje:string;nivel:string|null}
export interface SerieEvolucion {instrumento_id:string;nombre:string;version:string;puntos:PuntoEvolucion[];diferencia:string|null;tendencia:string}
export interface Evolucion {series:SerieEvolucion[]}
