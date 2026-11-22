import {inject,Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {API_URL} from '../../core/auth/api-url';
import {DatosFactor,RegistroFactor,HistorialFactores,TipoFactor} from './factores.models';
@Injectable({providedIn:'root'})
export class FactoresService {
 private http=inject(HttpClient);private base=inject(API_URL);
 historial(trabajador:string|null){return this.http.get<HistorialFactores>(this.base+(trabajador?'/psicologo/trabajadores/'+encodeURIComponent(trabajador)+'/factores/':'/trabajador/factores/'));}
 registrar(datos:DatosFactor){return this.http.post<RegistroFactor>(this.base+'/trabajador/factores/',datos);}
 tipos(){return this.http.get<TipoFactor[]>(this.base+'/catalogos/factores/');}
 guardarTipo(id:string|null,datos:Omit<TipoFactor,'id'>){return id?this.http.put<TipoFactor>(this.base+'/catalogos/factores/'+encodeURIComponent(id)+'/',datos):this.http.post<TipoFactor>(this.base+'/catalogos/factores/',datos);}
}
