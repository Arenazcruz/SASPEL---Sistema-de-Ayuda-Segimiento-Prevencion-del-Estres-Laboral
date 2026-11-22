import {DestroyRef,inject,Injectable,signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {ActivatedRoute} from '@angular/router';
import {finalize,Subscription} from 'rxjs';
import {AnimoService} from './animo.service';
import {HistorialAnimo} from './animo.models';
@Injectable()
export class AnimoViewModel {
 private api=inject(AnimoService);private destroy=inject(DestroyRef);private route=inject(ActivatedRoute);
 private reading?:Subscription;private writing?:Subscription;
 readonly trabajador=signal<string|null>(null);readonly datos=signal<HistorialAnimo|null>(null);
 readonly busy=signal(false);readonly error=signal('');readonly mensaje=signal('');
 estado='';intensidad='';comentario='';
 constructor(){this.route.paramMap.pipe(takeUntilDestroyed(this.destroy)).subscribe(p=>{this.reading?.unsubscribe();this.writing?.unsubscribe();this.trabajador.set(p.get('trabajadorId'));this.estado='';this.intensidad='';this.comentario='';this.mensaje.set('');this.load();});}
 load(){this.reading?.unsubscribe();this.datos.set(null);this.error.set('');this.busy.set(true);this.reading=this.api.historial(this.trabajador()).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:d=>this.datos.set(d),error:e=>this.fail(e)});}
 private fail(e:any){if([401,403,404].includes(e.status))this.datos.set(null);this.error.set([401,403,404].includes(e.status)?'No tienes acceso a este historial.':'No se pudo completar la solicitud. Revisa los datos e intenta nuevamente.');}
 guardar(){if(this.busy()||!this.datos()||this.trabajador())return;if(!this.estado.trim()||!this.intensidad.trim()){this.error.set('Indica cómo te sientes y su intensidad.');return;}this.busy.set(true);this.error.set('');this.mensaje.set('');this.writing=this.api.registrar({estado:this.estado.trim(),intensidad:this.intensidad.trim(),comentario:this.comentario.trim()}).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:r=>{this.datos.update(d=>d?{...d,registros:[...d.registros,r]}:null);this.estado='';this.intensidad='';this.comentario='';this.mensaje.set('Estado de ánimo registrado.');},error:e=>this.fail(e)});}
}
