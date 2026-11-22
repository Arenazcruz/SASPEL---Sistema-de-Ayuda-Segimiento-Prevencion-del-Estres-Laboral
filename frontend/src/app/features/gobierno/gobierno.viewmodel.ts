import {DestroyRef,inject,Injectable,signal} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {finalize} from 'rxjs';
import {GobiernoService} from './gobierno.service';
import {Politica,Eventos} from './gobierno.models';
import {apiError} from '../superadmin/superadmin.service';
@Injectable()
export class GobiernoViewModel {
 private api=inject(GobiernoService);private destroy=inject(DestroyRef);
 readonly modo=inject(ActivatedRoute).snapshot.data['modo'] as string;
 readonly politicas=signal<Politica[]|null>(null);readonly eventos=signal<Eventos|null>(null);
 readonly busy=signal(false);readonly error=signal('');readonly mensaje=signal('');desde='';hasta='';actor='';accion='';entidad='';page=1;
 form={tipo:'TERMINOS_USO',titulo:'',version:'',contenido:'',obligatoria:true};confirmacion=false;
 constructor(){this.load();}
 load(){if(this.busy())return;this.busy.set(true);this.error.set('');
  if(this.modo==='politicas'){this.politicas.set(null);this.api.politicas().pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:r=>this.politicas.set(r),error:e=>this.error.set(apiError(e))});}
  else {this.eventos.set(null);this.api.auditoria(this.page,this.desde,this.hasta,this.actor,this.accion,this.entidad).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:r=>this.eventos.set(r),error:e=>this.error.set(apiError(e))});}
 }
 filtrar(){if(this.desde&&this.hasta&&this.desde>this.hasta){this.error.set("La fecha final debe ser igual o posterior a la inicial.");return;}this.page=1;this.load();}
 pagina(delta:number){if(this.busy()||this.page+delta<1)return;this.page+=delta;this.load();}
 publicar(){if(this.busy())return;if(!this.form.titulo.trim()||!this.form.version.trim()||!this.form.contenido.trim()||!this.confirmacion){this.error.set('Completa la política y confirma su publicación.');return;}
  this.busy.set(true);this.error.set('');this.mensaje.set('');let guardado=false;
  this.api.publicar({...this.form}).pipe(takeUntilDestroyed(this.destroy),finalize(()=>{this.busy.set(false);if(guardado&&!this.destroy.destroyed)this.load();})).subscribe({next:()=>{guardado=true;this.form={tipo:'TERMINOS_USO',titulo:'',version:'',contenido:'',obligatoria:true};this.confirmacion=false;this.mensaje.set('Versión publicada. Las políticas obligatorias requieren nueva aceptación.');},error:e=>this.error.set(apiError(e))});
 }
}
