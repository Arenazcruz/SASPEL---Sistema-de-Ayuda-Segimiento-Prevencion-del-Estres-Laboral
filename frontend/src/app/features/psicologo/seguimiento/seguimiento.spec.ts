import {TestBed} from '@angular/core/testing';
import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting,HttpTestingController} from '@angular/common/http/testing';
import {ActivatedRoute,convertToParamMap,provideRouter} from '@angular/router';
import {BehaviorSubject} from 'rxjs';
import {API_URL} from '../../../core/auth/api-url';
import {SeguimientoComponent} from './seguimiento';
describe('Seguimiento profesional',()=>{
 let http:HttpTestingController;let params:BehaviorSubject<any>;const url='/api/psicologo/trabajadores/w/seguimiento/';
 beforeEach(()=>{params=new BehaviorSubject(convertToParamMap({trabajadorId:'w'}));TestBed.configureTestingModule({providers:[provideHttpClient(),provideHttpClientTesting(),provideRouter([]),{provide:API_URL,useValue:'/api'},{provide:ActivatedRoute,useValue:{paramMap:params}}]});http=TestBed.inject(HttpTestingController);});
 afterEach(()=>http.verify());
 function open(){const f=TestBed.createComponent(SeguimientoComponent);f.detectChanges();http.expectOne(url).flush({trabajador:'Ana',registros:[]});f.detectChanges();return f;}
 function fill(vm:any){vm.form={motivo:'Revisión',categoria:'Seguimiento',observacion:'Privado',estado:'Abierto',evolucion:'Estable',plan_accion:'Plan',proxima_revision:null};}
 it('muestra vacío, valida y conserva el formulario si falla',()=>{const f=open(),vm=f.componentInstance.vm;expect(f.nativeElement.textContent).toContain('Sin seguimientos');vm.guardar();http.expectNone(url);fill(vm);vm.guardar();vm.guardar();const r=http.expectOne(url);expect(r.request.body.trabajador_id).toBeUndefined();r.flush({}, {status:400,statusText:'Invalid'});expect(vm.form.observacion).toBe('Privado');expect(vm.busy()).toBe(false);});
 it('guarda y muestra la evolución cronológica',()=>{const f=open(),vm=f.componentInstance.vm;fill(vm);vm.guardar();http.expectOne(url).flush({...vm.form,id:'s',fecha:'2026-10-16T12:00:00Z',profesional:'Profesional'});f.detectChanges();expect(f.nativeElement.textContent).toContain('Estable');expect(f.nativeElement.textContent).toContain('Último estado registrado');expect(vm.form.observacion).toBe('');});
 it('cambio de trabajador cancela lectura anterior y limpia datos',()=>{const f=TestBed.createComponent(SeguimientoComponent);f.detectChanges();const old=http.expectOne(url);params.next(convertToParamMap({trabajadorId:'otro'}));expect(old.cancelled).toBe(true);http.expectOne('/api/psicologo/trabajadores/otro/seguimiento/').flush({}, {status:404,statusText:'Not Found'});expect(f.componentInstance.vm.datos()).toBeNull();});
 it('oculta errores internos y conserva la observación al fallar el guardado',()=>{
  const f=open(),vm=f.componentInstance.vm;fill(vm);vm.guardar();
  http.expectOne(url).flush({detail:'Traceback SQL secreto'}, {status:500,statusText:'Server error'});
  expect(vm.error()).not.toContain('secreto');expect(vm.form.observacion).toBe('Privado');expect(vm.busy()).toBe(false);
 });
});
