import {DestroyRef,inject,Injectable,signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {finalize} from 'rxjs';
import {PerfilService} from './perfil.service';
import {Perfil} from './perfil.models';
import {apiError} from '../superadmin/superadmin.service';
@Injectable()
export class PerfilViewModel {
 private api=inject(PerfilService);private destroy=inject(DestroyRef);
 readonly datos=signal<Perfil|null>(null);readonly busy=signal(false);readonly error=signal('');readonly mensaje=signal('');
 form={first_name:'',last_name:'',apellido_materno:'',telefono:'',fecha_nacimiento:'' as string|null,sexo:''};
 constructor(){this.load();}
 load(){if(this.busy())return;this.busy.set(true);this.error.set('');this.datos.set(null);this.api.consultar().pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:r=>{this.datos.set(r);for(const key of Object.keys(this.form) as (keyof typeof this.form)[])this.form[key]=r[key] as string;},error:e=>this.error.set(apiError(e))});}
 guardar(){if(this.busy())return;this.busy.set(true);this.error.set('');this.mensaje.set('');this.api.guardar({...this.form,fecha_nacimiento:this.form.fecha_nacimiento||null}).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:r=>{this.datos.set(r);this.mensaje.set('Perfil actualizado.');},error:e=>this.error.set(apiError(e))});}
}
