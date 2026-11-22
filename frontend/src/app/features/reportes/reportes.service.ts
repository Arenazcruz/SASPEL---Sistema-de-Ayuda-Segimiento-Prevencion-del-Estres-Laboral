import {inject,Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {API_URL} from '../../core/auth/api-url';
export interface Reporte {tipo:string;columnas:string[];filas:(string|number|boolean|null)[][];total:number;pagina:number;por_pagina:number;agregado:boolean;}
export interface Catalogos {areas:{id:string;nombre:string}[];instrumentos:{id:string;nombre:string;version:string}[];}
@Injectable({providedIn:'root'})
export class ReportesService {
 private http=inject(HttpClient);private base=inject(API_URL);
 catalogos(){return this.http.get<Catalogos>(this.base+'/reportes/catalogos/');}
 consultar(tipo:string,params:Record<string,string>){return this.http.get<Reporte>(this.base+'/reportes/'+tipo+'/',{params});}
 exportar(tipo:string,params:Record<string,string>){return this.http.get(this.base+'/reportes/'+tipo+'/',{params:{...params,formato:'csv'},responseType:'blob'});}
 descargar(blob:Blob,tipo:string){const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download='saspel-'+tipo+'.csv';link.click();URL.revokeObjectURL(url);}
}
