import {DestroyRef,inject,Injectable,signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {ActivatedRoute} from '@angular/router';
import {finalize,Subscription} from 'rxjs';
import {SeguimientoService} from './seguimiento.service';
import {DatosSeguimiento,HistorialSeguimiento} from './seguimiento.models';
const vacio=():DatosSeguimiento=>({motivo:'',categoria:'',observacion:'',estado:'',evolucion:'',plan_accion:'',proxima_revision:null});
@Injectable()
export class SeguimientoViewModel {
 private reading?:Subscription;private writing?:Subscription;
 private api=inject(SeguimientoService);private destroy=inject(DestroyRef);private route=inject(ActivatedRoute);private trabajador='';
 readonly datos=signal<HistorialSeguimiento|null>(null);readonly busy=signal(false);readonly error=signal('');readonly mensaje=signal('');
 form=vacio();
 constructor(){this.route.paramMap.pipe(takeUntilDestroyed(this.destroy)).subscribe(p=>{this.reading?.unsubscribe();this.writing?.unsubscribe();this.mensaje.set('');this.trabajador=p.get('trabajadorId')??'';this.form=vacio();this.load();});}
 load(){this.datos.set(null);this.error.set('');this.busy.set(true);this.reading=this.api.historial(this.trabajador).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:d=>this.datos.set(d),error:e=>this.fail(e)});}
 private fail(e:any){if([401,403,404].includes(e.status))this.datos.set(null);this.error.set([401,403,404].includes(e.status)?'No tienes acceso a este seguimiento.':typeof e.error?.detail==='string'?e.error.detail:'No se pudo guardar o consultar. Revisa los datos e intenta nuevamente.');}
 guardar(){if(this.busy()||!this.datos())return;const f=this.form;if([f.motivo,f.categoria,f.observacion,f.estado,f.evolucion,f.plan_accion].some(x=>!x.trim())){this.error.set('Completa todos los campos del seguimiento.');return;}
 this.busy.set(true);this.error.set('');this.mensaje.set('');this.writing=this.api.registrar(this.trabajador,{...f,proxima_revision:f.proxima_revision||null}).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:r=>{this.datos.update(d=>d?{...d,registros:[...d.registros,r]}:null);this.form=vacio();this.mensaje.set('Seguimiento registrado.');},error:e=>this.fail(e)});}
}
