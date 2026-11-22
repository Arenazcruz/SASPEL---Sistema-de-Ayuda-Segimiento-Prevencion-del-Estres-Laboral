import {DestroyRef,inject,Injectable,signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {finalize,Subscription} from 'rxjs';
import {AuthService} from '../../core/auth/auth.service';
import {NotificacionesService,Notificacion,Alerta} from './notificaciones.service';
@Injectable()
export class NotificacionesViewModel {
 private api=inject(NotificacionesService);private destroy=inject(DestroyRef);readonly auth=inject(AuthService);
 readonly datos=signal<Notificacion[]|null>(null);readonly alertas=signal<Alerta[]|null>(null);
 readonly loading=signal(false);readonly busy=signal(false);readonly error=signal('');readonly alertError=signal('');
 pendientes=false;private reading?:Subscription;
 constructor(){this.load();if(this.auth.user()?.role==='PSICOLOGO')this.loadAlertas();}
 load(){this.reading?.unsubscribe();this.datos.set(null);this.error.set('');this.loading.set(true);this.reading=this.api.listar(this.pendientes).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.loading.set(false))).subscribe({next:d=>this.datos.set(d),error:()=>this.error.set('No se pudieron consultar las notificaciones.')});}
 leer(row:Notificacion){if(this.busy()||row.leida_en)return;this.busy.set(true);this.error.set('');this.api.leer(row.id).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:r=>this.datos.update(d=>d?.map(x=>x.id===r.id?{...x,leida_en:r.leida_en}:x).filter(x=>!this.pendientes||!x.leida_en)??null),error:()=>{this.datos.set(null);this.error.set('No se pudo actualizar la notificación. Recarga para comprobar tu acceso.');}});}
 loadAlertas(){this.alertas.set(null);this.alertError.set('');this.api.alertas().pipe(takeUntilDestroyed(this.destroy)).subscribe({next:d=>this.alertas.set(d),error:()=>this.alertError.set('No se pudieron consultar las alertas autorizadas.')});}
 actuar(row:Alerta,estado:string,observacion:string){if(this.busy())return;if(!observacion.trim()){this.alertError.set('Escribe la acción realizada.');return;}this.busy.set(true);this.alertError.set('');this.api.actuar(row.id,estado,observacion.trim()).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:r=>this.alertas.update(a=>a?.map(x=>x.id===r.id?r:x)??null),error:()=>{this.alertas.set(null);this.alertError.set('No se pudo registrar la acción. Comprueba el estado y tu asignación.');}});}
}
