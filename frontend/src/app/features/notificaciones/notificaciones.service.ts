import {inject,Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {API_URL} from '../../core/auth/api-url';
export interface Notificacion {id:string;tipo:string;titulo:string;origen_id:string;creado_en:string;leida_en:string|null;}
export interface Alerta {id:string;trabajador:string;trabajador_id:string;resultado_id:string;regla:string;nivel:string;estado:string;fecha:string;acciones:{id:string;estado:string;observacion:string;creado_en:string;creado_por:string}[];}
@Injectable({providedIn:'root'})
export class NotificacionesService {
 private http=inject(HttpClient);private base=inject(API_URL);
 listar(pendientes=false){return this.http.get<Notificacion[]>(this.base+'/notificaciones/',{params:{pendientes}});}
 leer(id:string){return this.http.post<{id:string;leida_en:string}>(this.base+'/notificaciones/'+id+'/leer/',{});}
 alertas(){return this.http.get<Alerta[]>(this.base+'/alertas/');}
 actuar(id:string,estado:string,observacion:string){return this.http.post<Alerta>(this.base+'/alertas/'+id+'/acciones/',{estado,observacion});}
}
