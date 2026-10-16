import {DestroyRef,inject,Injectable,signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {Subscription,finalize} from 'rxjs';
import {AuthService} from '../../core/auth/auth.service';
import {ReportesService,Reporte,Catalogos} from './reportes.service';
@Injectable()
export class ReportesViewModel {
 private api=inject(ReportesService);private destroy=inject(DestroyRef);private reading?:Subscription;readonly auth=inject(AuthService);
 readonly datos=signal<Reporte|null>(null);readonly catalogos=signal<Catalogos|null>(null);readonly loading=signal(false);readonly exporting=signal(false);readonly error=signal('');
 tipo='usuarios';desde='';hasta='';estado='';area='';instrumento='';pagina=1;
 constructor(){this.api.catalogos().pipe(takeUntilDestroyed(this.destroy)).subscribe({next:d=>this.catalogos.set(d),error:()=>this.error.set('No se pudieron cargar los filtros. Recarga la página.')});this.load();}
 params(){const p:Record<string,string>={pagina:String(this.pagina)};for(const k of ['desde','hasta','estado','area','instrumento'] as const)if(this[k])p[k]=this[k];return p;}
 cambiar(){this.estado='';this.area='';this.instrumento='';this.pagina=1;this.load();}
 load(){this.reading?.unsubscribe();this.datos.set(null);this.error.set('');if(this.desde&&this.hasta&&this.desde>this.hasta){this.error.set('Revisa el intervalo de fechas.');return;}this.loading.set(true);this.reading=this.api.consultar(this.tipo,this.params()).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.loading.set(false))).subscribe({next:d=>this.datos.set(d),error:()=>this.error.set('No se pudo consultar el reporte. Revisa los filtros y tu acceso.')});}
 buscar(){this.pagina=1;this.load();}
 mover(delta:number){this.pagina+=delta;this.load();}
 exportar(){if(this.exporting()||this.loading()||!this.datos())return;this.exporting.set(true);this.error.set('');const tipo=this.tipo;this.api.exportar(tipo,this.params()).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.exporting.set(false))).subscribe({next:b=>this.api.descargar(b,tipo),error:()=>this.error.set('No se pudo exportar. Comprueba el acceso o reduce los filtros (máximo 10000 filas).')});}
}
