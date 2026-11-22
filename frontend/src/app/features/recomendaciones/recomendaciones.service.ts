import {inject,Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {API_URL} from '../../core/auth/api-url';
import {Recomendacion} from './recomendaciones.models';
@Injectable({providedIn:'root'})
export class RecomendacionesService {
 private http=inject(HttpClient);private base=inject(API_URL);
 private url(id:string){return this.base+'/seguimientos/'+encodeURIComponent(id)+'/recomendaciones/';}
 listar(id:string){return this.http.get<Recomendacion[]>(this.url(id));}
 crear(id:string,texto:string){return this.http.post<Recomendacion>(this.url(id),{texto});}
 cambiar(id:string,recomendacion:string,estado:string){return this.http.post<Recomendacion>(this.url(id)+encodeURIComponent(recomendacion)+'/estado/',{estado});}
}
