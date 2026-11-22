import {inject,Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {API_URL} from '../../core/auth/api-url';
import {Perfil} from './perfil.models';
@Injectable({providedIn:'root'})
export class PerfilService {
 private http=inject(HttpClient);private url=inject(API_URL)+'/perfil/';
 consultar(){return this.http.get<Perfil>(this.url);}
 guardar(datos:object){return this.http.patch<Perfil>(this.url,datos);}
}
