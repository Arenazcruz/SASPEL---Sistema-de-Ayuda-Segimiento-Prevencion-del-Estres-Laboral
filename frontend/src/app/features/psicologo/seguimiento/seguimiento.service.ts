import {inject,Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {API_URL} from '../../../core/auth/api-url';
import {DatosSeguimiento,HistorialSeguimiento,Seguimiento} from './seguimiento.models';
@Injectable({providedIn:'root'})
export class SeguimientoService {
 private http=inject(HttpClient); private base=inject(API_URL);
 private url(id:string){return this.base+'/psicologo/trabajadores/'+encodeURIComponent(id)+'/seguimiento/';}
 historial(id:string){return this.http.get<HistorialSeguimiento>(this.url(id));}
 registrar(id:string,datos:DatosSeguimiento){return this.http.post<Seguimiento>(this.url(id),datos);}
}
