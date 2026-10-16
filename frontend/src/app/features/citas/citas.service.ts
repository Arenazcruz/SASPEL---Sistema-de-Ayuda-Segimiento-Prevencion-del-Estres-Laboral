import {inject,Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {API_URL} from '../../core/auth/api-url';
import {Cita,Bloque,ContextoCita} from './citas.models';
@Injectable({providedIn:'root'})
export class CitasService {
 private http=inject(HttpClient); private base=inject(API_URL);
 listar(){return this.http.get<Cita[]>(this.base+'/citas/');}
 contexto(){return this.http.get<ContextoCita>(this.base+'/citas/contexto/');}
 solicitar(datos:object){return this.http.post<Cita>(this.base+'/citas/',datos);}
 accion(id:string,accion:string,motivo:string){return this.http.post<Cita>(this.base+'/citas/'+encodeURIComponent(id)+'/'+accion+'/',{motivo});}
 disponibilidad(){return this.http.get<Bloque[]>(this.base+'/psicologo/disponibilidad/');}
 guardarBloque(datos:object){return this.http.post<Bloque[]>(this.base+'/psicologo/disponibilidad/',datos);}
 desactivar(id:string){return this.http.post<Bloque[]>(this.base+'/psicologo/disponibilidad/'+encodeURIComponent(id)+'/desactivar/',{});}
}
