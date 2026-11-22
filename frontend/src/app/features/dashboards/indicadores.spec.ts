import {TestBed} from '@angular/core/testing';
import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting,HttpTestingController} from '@angular/common/http/testing';
import {API_URL} from '../../core/auth/api-url';
import {IndicadoresComponent} from './indicadores';
describe('Indicadores por rol',()=>{
 let http:HttpTestingController;
 beforeEach(()=>{TestBed.configureTestingModule({providers:[provideHttpClient(),provideHttpClientTesting(),{provide:API_URL,useValue:'/api'}]});http=TestBed.inject(HttpTestingController);});
 afterEach(()=>http.verify());
 it('muestra datos recibidos y actualiza sin valores fijos',()=>{const f=TestBed.createComponent(IndicadoresComponent);f.detectChanges();expect(f.nativeElement.textContent).toContain('Cargando');http.expectOne('/api/dashboard/').flush({rol:'PSICOLOGO',actualizado:'2026-10-16',indicadores:[{clave:'trabajadores',etiqueta:'Trabajadores asignados',valor:17}]});f.detectChanges();expect(f.nativeElement.textContent).toContain('17');f.componentInstance.vm.load();expect(f.componentInstance.vm.datos()).toBeNull();http.expectOne('/api/dashboard/').flush({rol:'PSICOLOGO',indicadores:[{clave:'trabajadores',etiqueta:'Trabajadores asignados',valor:0}]});f.detectChanges();expect(f.nativeElement.textContent).toContain('No hay actividad');});
 it('error no conserva datos de acceso anterior',()=>{const f=TestBed.createComponent(IndicadoresComponent);http.expectOne('/api/dashboard/').flush({}, {status:403,statusText:'Forbidden'});f.detectChanges();expect(f.componentInstance.vm.datos()).toBeNull();expect(f.nativeElement.textContent).toContain('No se pudieron cargar');});
});
