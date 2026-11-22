import {inject,Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {API_URL} from '../../core/auth/api-url';
import {Asignaciones,AsignacionInstrumento} from './asignaciones.models';
@Injectable({providedIn:'root'})
export class AsignacionesInstrumentoService {
 private http=inject(HttpClient);private base=inject(API_URL);
 private url(id:string|null){return this.base+(id?'/psicologo/trabajadores/'+encodeURIComponent(id)+'/instrumentos/':'/trabajador/instrumentos/');}
 listar(id:string|null){return this.http.get<Asignaciones>(this.url(id));}
 asignar(id:string,datos:object){return this.http.post<AsignacionInstrumento>(this.url(id),datos);}
}
