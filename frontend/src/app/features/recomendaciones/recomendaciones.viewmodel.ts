import {DestroyRef,inject,Injectable,signal} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {finalize,Observable} from 'rxjs';
import {RecomendacionesService} from './recomendaciones.service';
import {Recomendacion} from './recomendaciones.models';
import {apiError} from '../superadmin/superadmin.service';
@Injectable()
export class RecomendacionesViewModel {
 private api=inject(RecomendacionesService);private destroy=inject(DestroyRef);
 readonly id=inject(ActivatedRoute).snapshot.paramMap.get('seguimientoId')!;
 readonly datos=signal<Recomendacion[]|null>(null);readonly busy=signal(false);readonly error=signal('');readonly mensaje=signal('');texto='';
 compartida=false;
 readonly propias=!this.id;
 constructor(){this.load();}
 load(){if(this.busy())return;this.busy.set(true);this.datos.set(null);this.error.set('');(this.propias?this.api.propias():this.api.listar(this.id)).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:r=>this.datos.set(r),error:e=>this.error.set(apiError(e))});}
 guardar(){if(!this.texto.trim()||this.texto.trim().length>5000){this.error.set('Escribe una recomendación de hasta 5000 caracteres.');return;}this.enviar(this.api.crear(this.id,this.texto.trim(),this.compartida),true);}
 cambiar(r:Recomendacion,estado:string){this.enviar(this.api.cambiar(this.id,r.id,estado));}
 private enviar(request:Observable<unknown>,limpiar=false){if(this.busy())return;this.busy.set(true);this.error.set('');this.mensaje.set('');let guardado=false;request.pipe(takeUntilDestroyed(this.destroy),finalize(()=>{this.busy.set(false);if(guardado&&!this.destroy.destroyed)this.load();})).subscribe({next:()=>{guardado=true;if(limpiar){this.texto='';this.compartida=false;}this.mensaje.set('Recomendación guardada.');},error:e=>this.error.set(apiError(e))});}
}
