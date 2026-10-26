import {DestroyRef,inject,Injectable,signal} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {finalize} from 'rxjs';
import {EvolucionService} from './evolucion.service';
import {Evolucion,SerieEvolucion} from './evolucion.models';
import {apiError} from '../superadmin/superadmin.service';
@Injectable()
export class EvolucionViewModel {
 private api=inject(EvolucionService);private destroy=inject(DestroyRef);
 readonly trabajador=inject(ActivatedRoute).snapshot.paramMap.get('trabajadorId');
 readonly datos=signal<Evolucion|null>(null);readonly busy=signal(false);readonly error=signal('');desde='';hasta='';
 readonly tendencias:Record<string,string>={SIN_COMPARACION:'Un resultado: todavía no hay comparación',AUMENTO:'Aumento del puntaje',DISMINUCION:'Disminución del puntaje',SIN_CAMBIO:'Sin cambio de puntaje'};
 constructor(){this.load();}
 load(){if(this.busy())return;if(this.desde&&this.hasta&&this.desde>this.hasta){this.error.set('Revisa el orden de las fechas.');return;}this.busy.set(true);this.datos.set(null);this.error.set('');this.api.consultar(this.trabajador,this.desde,this.hasta).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:r=>this.datos.set(r),error:e=>this.error.set(apiError(e))});}
 puntos(s:SerieEvolucion){const valores=s.puntos.map(p=>Number(p.puntaje)),min=Math.min(...valores),max=Math.max(...valores);const fechas=s.puntos.map(p=>new Date(p.fecha).getTime()),a=fechas[0],b=fechas.at(-1)!;return valores.map((v,i)=>`${20+(b>a?(fechas[i]-a)/(b-a):.5)*560},${max>min?150-(v-min)/(max-min)*120:90}`).join(' ');}
}
