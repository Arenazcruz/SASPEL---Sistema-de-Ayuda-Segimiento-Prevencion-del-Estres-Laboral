import {DestroyRef,inject,Injectable,signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {ActivatedRoute} from '@angular/router';
import {finalize,forkJoin,of,Subscription} from 'rxjs';
import {FactoresService} from './factores.service';
import {HistorialFactores,TipoFactor} from './factores.models';
import {apiError} from '../superadmin/superadmin.service';
@Injectable()
export class FactoresViewModel {
 private api=inject(FactoresService);private destroy=inject(DestroyRef);private route=inject(ActivatedRoute);
 private reading?:Subscription;private writing?:Subscription;
 readonly trabajador=signal<string|null>(null);readonly datos=signal<HistorialFactores|null>(null);readonly tipos=signal<TipoFactor[]>([]);
 readonly busy=signal(false);readonly error=signal('');readonly mensaje=signal('');
 tipo='';nivel='';descripcion='';
 constructor(){this.route.paramMap.pipe(takeUntilDestroyed(this.destroy)).subscribe(p=>{this.reading?.unsubscribe();this.writing?.unsubscribe();this.trabajador.set(p.get('trabajadorId'));this.tipo='';this.nivel='';this.descripcion='';this.mensaje.set('');this.load();});}
 load(){this.reading?.unsubscribe();this.datos.set(null);this.tipos.set([]);this.error.set('');this.busy.set(true);this.reading=forkJoin({historial:this.api.historial(this.trabajador()),tipos:this.trabajador()?of([] as TipoFactor[]):this.api.tipos()}).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:d=>{this.datos.set(d.historial);this.tipos.set(d.tipos);},error:e=>this.fail(e)});}
 private fail(e:any){if([401,403,404].includes(e.status)){this.datos.set(null);this.tipos.set([]);}this.error.set([401,403,404].includes(e.status)?'No tienes acceso a este historial.':apiError(e));}
 guardar(){if(this.busy()||!this.datos()||this.trabajador())return;if(!this.tipos().some(t=>t.id===this.tipo)||!this.nivel.trim()||!this.descripcion.trim()){this.error.set('Selecciona un factor e indica nivel y descripción.');return;}this.busy.set(true);this.error.set('');this.mensaje.set('');this.writing=this.api.registrar({tipo_id:this.tipo,nivel:this.nivel.trim(),descripcion:this.descripcion.trim()}).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:r=>{this.datos.update(d=>d?{...d,registros:[...d.registros,r]}:null);this.tipo='';this.nivel='';this.descripcion='';this.mensaje.set('Factor registrado.');},error:e=>this.fail(e)});}
}
