import {Component, DestroyRef, inject, Injectable, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {ActivatedRoute, RouterLink} from '@angular/router';
import {finalize, forkJoin} from 'rxjs';
import {ADMINISTRATION_CONTEXT} from '../administration-context';
import {Institution} from '../superadmin.models';
import {apiError, SuperadminService} from '../superadmin.service';

@Injectable()
export class AreaCargosViewModel {
  private readonly api=inject(SuperadminService);
  private readonly destroy=inject(DestroyRef);
  private readonly id=inject(ActivatedRoute).snapshot.paramMap.get('id')!;
  readonly panel=inject(ADMINISTRATION_CONTEXT).panel;
  readonly area=signal('área');readonly cargos=signal<Institution[]>([]);
  readonly selected=signal<string[]>([]);readonly loading=signal(false);readonly busy=signal(false);
  readonly ready=signal(false);readonly error=signal('');readonly notice=signal('');
  constructor(){this.load();}
  load(){
    this.loading.set(true);this.ready.set(false);this.error.set('');
    forkJoin({areas:this.api.institution('areas'), cargos:this.api.institution('cargos'), links:this.api.areaCargos(this.id)})
      .pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.loading.set(false))).subscribe({
        next:({areas,cargos,links})=>{
          const area=areas.find(a=>a.id===this.id);this.area.set(area?.nombre||'área');
          this.cargos.set(cargos);this.selected.set(links.cargo_ids.filter(id=>cargos.some(c=>c.id===id&&c.activo)));
          this.ready.set(!!area?.activo);
          if(!area?.activo)this.error.set('Activa el área antes de configurar sus cargos.');
        },error:e=>this.error.set(apiError(e)),
      });
  }
  toggle(id:string,event:Event){
    const checked=(event.target as HTMLInputElement).checked;
    this.selected.update(ids=>checked?[...ids,id]:ids.filter(x=>x!==id));
  }
  save(){
    if(this.busy()||!this.ready())return;
    this.busy.set(true);this.error.set('');this.notice.set('');
    this.api.saveAreaCargos(this.id,this.selected()).pipe(takeUntilDestroyed(this.destroy),finalize(()=>this.busy.set(false)))
      .subscribe({next:()=>this.notice.set('Cargos del área actualizados.'),error:e=>this.error.set(apiError(e))});
  }
}

@Component({
  selector:'app-area-cargos', imports:[RouterLink], providers:[AreaCargosViewModel],
  template:`
    <p class="eyebrow">ADMINISTRACIÓN / INSTITUCIÓN</p>
    <h1>Cargos de {{vm.area()}}</h1>
    <a [routerLink]="[vm.panel, 'institucion', 'areas']">Volver a áreas</a>
    <p>Selecciona los cargos disponibles para nuevas asignaciones en esta área. Los perfiles existentes conservan su información.</p>
    @if(vm.error()){<p class="sa-error" role="alert">{{vm.error()}} <button (click)="vm.load()">Reintentar</button></p>}
    @if(vm.notice()){<p class="sa-success" role="status">{{vm.notice()}}</p>}
    @if(vm.loading()){<p role="status">Cargando cargos…</p>}
    @else {
      <section class="sa-panel">
        @for(cargo of vm.cargos(); track cargo.id){
          <p><label><input type="checkbox" [checked]="vm.selected().includes(cargo.id)"
            [disabled]="vm.busy() || !cargo.activo" (change)="vm.toggle(cargo.id, $event)" /> {{cargo.nombre}}{{cargo.activo?'':' (inactivo)'}}</label></p>
        } @empty {<p>Crea primero los cargos en el catálogo institucional.</p>}
        <button class="button button-small" [disabled]="vm.busy() || !vm.ready()" (click)="vm.save()">Guardar cargos del área</button>
      </section>
    }
  `,
})
export class AreaCargos { readonly vm=inject(AreaCargosViewModel); }
