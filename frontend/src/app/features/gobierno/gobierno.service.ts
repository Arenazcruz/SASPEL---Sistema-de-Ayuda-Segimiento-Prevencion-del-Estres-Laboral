import {inject,Injectable} from '@angular/core';
import {HttpClient,HttpParams} from '@angular/common/http';
import {API_URL} from '../../core/auth/api-url';
import {Politica,Eventos} from './gobierno.models';
@Injectable({providedIn:'root'})
export class GobiernoService {
 private http=inject(HttpClient);private base=inject(API_URL)+'/administracion/';
 politicas(){return this.http.get<Politica[]>(this.base+'politicas/');}
 publicar(datos:object){return this.http.post<Politica>(this.base+'politicas/',datos);}
 auditoria(page:number,desde:string,hasta:string){let params=new HttpParams().set('page',page);if(desde)params=params.set('desde',desde);if(hasta)params=params.set('hasta',hasta);return this.http.get<Eventos>(this.base+'auditoria/',{params});}
}
