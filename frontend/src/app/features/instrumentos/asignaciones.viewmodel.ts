import {DestroyRef,inject,Injectable,signal} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {finalize} from 'rxjs';
import {AsignacionesInstrumentoService} from './asignaciones.service';
import {Asignaciones} from './asignaciones.models';
import {apiError} from '../superadmin/superadmin.service';
@Injectable()
export class AsignacionesInstrumentoViewModel {
 private api=inject(AsignacionesInstrumentoService);private destroy=inject(DestroyRef);
 readonly trabajador=inject(ActivatedRoute).snapshot.paramMap.get('trabajadorId');
 readonly regreso=inject(ActivatedRoute).snapshot.data?.['role']==='SUPERADMIN'?'/dashboard/superadmin/personas':(this.trabajador?'/dashboard/psicologo/trabajadores':'/dashboard/trabajador');
 readonly datos=signal<Asignaciones|null>(null);readonly busy=signal(false);readonly error=signal('');readonly mensaje=signal('');
 instrumento='';limite='';
 constructor(){this.load();}
 load(){if(this.busy())return;this.busy.set(true);this.datos.set(null);this.error.set('');this.api.listar(this.trabajador).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:r=>this.datos.set(r),error:e=>this.error.set(apiError(e))});}
 asignar(){if(this.busy()||!this.trabajador)return;const fecha=this.limite?new Date(this.limite):null;
  if(!this.instrumento||(fecha&&(!Number.isFinite(fecha.getTime())||fecha<=new Date()))){this.error.set('Selecciona un instrumento y una fecha límite futura, si corresponde.');return;}
  this.busy.set(true);this.error.set('');this.mensaje.set('');let guardado=false;
  this.api.asignar(this.trabajador,{instrumento_id:this.instrumento,fecha_limite:fecha?.toISOString()??null}).pipe(takeUntilDestroyed(this.destroy),finalize(()=>{this.busy.set(false);if(guardado&&!this.destroy.destroyed)this.load();})).subscribe({next:()=>{guardado=true;this.mensaje.set('Instrumento asignado.');this.instrumento='';this.limite='';},error:e=>this.error.set(apiError(e))});
 }
}
