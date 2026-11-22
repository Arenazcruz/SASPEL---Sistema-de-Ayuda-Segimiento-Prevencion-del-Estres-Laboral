import {DestroyRef,inject,Injectable,signal,computed} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {HttpClient} from '@angular/common/http';
import {Subscription,finalize} from 'rxjs';
import {API_URL} from '../../core/auth/api-url';
export interface Indicadores {rol:string;actualizado:string;indicadores:{clave:string;etiqueta:string;valor:number}[];}
@Injectable()
export class IndicadoresViewModel {
 private http=inject(HttpClient);private base=inject(API_URL);private destroy=inject(DestroyRef);private reading?:Subscription;
 readonly datos=signal<Indicadores|null>(null);readonly loading=signal(false);readonly error=signal('');
 readonly vacio=computed(()=>this.datos()?.indicadores.every(x=>x.valor===0)??false);
 constructor(){this.load();}
 load(){this.reading?.unsubscribe();this.datos.set(null);this.loading.set(true);this.error.set('');this.reading=this.http.get<Indicadores>(this.base+'/dashboard/').pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.loading.set(false))).subscribe({next:d=>this.datos.set(d),error:()=>this.error.set('No se pudieron cargar los indicadores. Reintenta para comprobar tu acceso.')});}
}
