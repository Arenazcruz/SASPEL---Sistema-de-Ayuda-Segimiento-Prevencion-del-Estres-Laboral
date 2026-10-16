import {inject,Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {API_URL} from '../../core/auth/api-url';
import {DatosAnimo,RegistroAnimo,HistorialAnimo} from './animo.models';
@Injectable({providedIn:'root'})
export class AnimoService {
 private http=inject(HttpClient);private base=inject(API_URL);
 historial(trabajador:string|null){return this.http.get<HistorialAnimo>(this.base+(trabajador?'/psicologo/trabajadores/'+encodeURIComponent(trabajador)+'/animo/':'/trabajador/animo/'));}
 registrar(datos:DatosAnimo){return this.http.post<RegistroAnimo>(this.base+'/trabajador/animo/',datos);}
}
