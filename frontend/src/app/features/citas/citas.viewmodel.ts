import {computed,DestroyRef,inject,Injectable,signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {finalize,forkJoin,Observable} from 'rxjs';
import {AuthService} from '../../core/auth/auth.service';
import {CitasService} from './citas.service';
import {Cita,Bloque,NotaCita} from './citas.models';
@Injectable()
export class CitasViewModel {
 private api=inject(CitasService); private auth=inject(AuthService); private destroy=inject(DestroyRef);
 readonly profesional=computed(()=>this.auth.user()?.role==='PSICOLOGO');
 readonly panel=computed(()=>this.auth.user()?.dashboard_path??'/login');
 readonly citas=signal<Cita[]>([]);readonly bloques=signal<Bloque[]>([]);readonly psicologo=signal<string|null>(null);
 readonly busy=signal(false);readonly ready=signal(false);readonly error=signal('');readonly mensaje=signal('');
 readonly dias=['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'];
 inicio='';fin='';motivo='';prioridad='MEDIA';dia=0;desde='';hasta='';cierres:Record<string,string>={};
 readonly notas=signal<Record<string,NotaCita[]>>({}); textos:Record<string,string>={};
 cargarNotas(id:string){if(this.busy()||!this.profesional())return;this.busy.set(true);this.error.set('');this.notas.update(n=>({...n,[id]:[]}));this.api.notas(id).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:r=>this.notas.update(n=>({...n,[id]:r})),error:e=>this.fail(e)});}
 guardarNota(id:string){const texto=this.textos[id]?.trim();if(!texto){this.error.set('Escribe una observación.');return;}this.enviar(this.api.guardarNota(id,texto),()=>{delete this.textos[id];});}
 puedeCompletar(c:Cita){return this.profesional()&&c.estado==='CONFIRMADA'&&new Date(c.fecha_fin)<=new Date();}
 constructor(){this.load();}
 load(){if(this.busy())return;this.busy.set(true);this.ready.set(false);this.error.set('');this.citas.set([]);this.bloques.set([]);this.notas.set({});
 const contexto:Observable<{psicologo:string|null;disponibilidad:Bloque[]}|Bloque[]>=this.profesional()?this.api.disponibilidad():this.api.contexto();
 forkJoin({citas:this.api.listar(),contexto}).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:({citas,contexto})=>{this.citas.set(citas);this.bloques.set(Array.isArray(contexto)?contexto:contexto.disponibilidad);this.psicologo.set(Array.isArray(contexto)?null:contexto.psicologo);this.ready.set(true);},error:e=>this.fail(e)});}
 private fail(e:any){this.error.set(e.status===401?'Tu sesión ya no es válida. Vuelve a iniciar sesión.':e.status===403||e.status===404?'No tienes acceso a esta información o ya no está disponible.':typeof e.error?.detail==='string'?e.error.detail:'No se pudo completar la solicitud. Revisa los datos e intenta nuevamente.');}
 private enviar(request:Observable<unknown>,done:()=>void){if(this.busy())return;this.busy.set(true);this.error.set('');this.mensaje.set('');request.pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false))).subscribe({next:()=>{done();this.mensaje.set('Cambios guardados.');this.busy.set(false);this.load();},error:e=>this.fail(e)});}
 solicitar(){if(this.busy()||!this.ready())return;const inicio=new Date(this.inicio),fin=new Date(this.fin);if(!this.motivo.trim()||!this.psicologo()||!Number.isFinite(inicio.getTime())||!Number.isFinite(fin.getTime())||inicio<=new Date()||fin<=inicio){this.error.set('Indica motivo y un horario futuro válido.');return;}
 this.enviar(this.api.solicitar({fecha_inicio:inicio.toISOString(),fecha_fin:fin.toISOString(),motivo:this.motivo.trim(),prioridad:this.prioridad}),()=>{this.inicio='';this.fin='';this.motivo='';});}
 accion(c:Cita,accion:string){const motivo=this.cierres[c.id]?.trim()??'';if(['rechazar','cancelar'].includes(accion)&&!motivo){this.error.set('Indica el motivo del cierre.');return;}this.enviar(this.api.accion(c.id,accion,motivo),()=>{delete this.cierres[c.id];});}
 guardarBloque(){if(!this.desde||!this.hasta||this.desde>=this.hasta){this.error.set('Indica un intervalo de horas válido.');return;}this.enviar(this.api.guardarBloque({dia_semana:Number(this.dia),hora_inicio:this.desde,hora_fin:this.hasta}),()=>{this.desde='';this.hasta='';});}
 desactivar(id:string){this.enviar(this.api.desactivar(id),()=>{});}
}
