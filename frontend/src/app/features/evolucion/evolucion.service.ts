import {inject,Injectable} from '@angular/core';
import {HttpClient,HttpParams} from '@angular/common/http';
import {API_URL} from '../../core/auth/api-url';
import {Evolucion} from './evolucion.models';
@Injectable({providedIn:'root'})
export class EvolucionService {
 private http=inject(HttpClient);private base=inject(API_URL);
 consultar(id:string|null,desde:string,hasta:string){let params=new HttpParams();if(desde)params=params.set('desde',desde);if(hasta)params=params.set('hasta',hasta);return this.http.get<Evolucion>(this.base+(id?'/psicologo/trabajadores/'+encodeURIComponent(id)+'/evolucion/':'/trabajador/evolucion/'),{params});}
}
