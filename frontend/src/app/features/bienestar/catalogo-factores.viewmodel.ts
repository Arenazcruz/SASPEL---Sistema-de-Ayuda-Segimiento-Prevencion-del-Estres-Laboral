import {DestroyRef,inject,Injectable,signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {finalize} from 'rxjs';
import {AuthService} from '../../core/auth/auth.service';
import {FactoresService} from './factores.service';
import {TipoFactor} from './factores.models';
@Injectable()
export class CatalogoFactoresViewModel {
 private api=inject(FactoresService);private destroy=inject(DestroyRef);private auth=inject(AuthService);
 readonly panel=this.auth.user()?.dashboard_path??'/login';readonly tipos=signal<TipoFactor[]>([]);readonly busy=signal(false);readonly ready=signal(false);readonly error=signal('');readonly mensaje=signal('');
 id:string|null=null;nombre='';descripcion='';activo=true;
 constructor(){this.load();}
 load(){this.busy.set(true);this.ready.set(false);this.tipos.set([]);this.error.set('');this.api.tipos().pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:r=>{this.tipos.set(r);this.ready.set(true);},error:e=>this.fail(e)});}
 editar(t:TipoFactor){this.id=t.id;this.nombre=t.nombre;this.descripcion=t.descripcion;this.activo=t.activo;this.error.set('');this.mensaje.set('');}
 limpiar(){this.id=null;this.nombre='';this.descripcion='';this.activo=true;}
 private fail(e:any){if([401,403,404].includes(e.status)){this.tipos.set([]);this.ready.set(false);}this.error.set([401,403,404].includes(e.status)?'No tienes acceso al catálogo.':typeof e.error?.detail==='string'?e.error.detail:'No se pudo guardar. Revisa los datos e intenta nuevamente.');}
 guardar(){if(this.busy()||!this.ready())return;if(!this.nombre.trim()){this.error.set('Indica el nombre del tipo.');return;}this.busy.set(true);this.error.set('');this.mensaje.set('');this.api.guardarTipo(this.id,{nombre:this.nombre.trim(),descripcion:this.descripcion.trim(),activo:this.activo}).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:r=>{this.tipos.update(rows=>[...rows.filter(t=>t.id!==r.id),r].sort((a,b)=>a.nombre.localeCompare(b.nombre)));this.limpiar();this.mensaje.set('Tipo guardado.');},error:e=>this.fail(e)});}
}
