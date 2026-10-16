import {TestBed} from '@angular/core/testing';
import {signal} from '@angular/core';
import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting,HttpTestingController} from '@angular/common/http/testing';
import {ActivatedRoute,convertToParamMap,provideRouter} from '@angular/router';
import {BehaviorSubject} from 'rxjs';
import {API_URL} from '../../core/auth/api-url';
import {AuthService} from '../../core/auth/auth.service';
import {FactoresComponent} from './factores';
import {CatalogoFactoresComponent} from './catalogo-factores';
describe('Factores psicosociales',()=>{
 let http:HttpTestingController;let params:BehaviorSubject<any>;const url='/api/trabajador/factores/',cat='/api/catalogos/factores/';const tipo={id:'t',nombre:'Tipo institucional',descripcion:'Descripción',activo:true};
 beforeEach(()=>{params=new BehaviorSubject(convertToParamMap({}));TestBed.configureTestingModule({providers:[provideHttpClient(),provideHttpClientTesting(),provideRouter([]),{provide:API_URL,useValue:'/api'},{provide:ActivatedRoute,useValue:{paramMap:params}},{provide:AuthService,useValue:{user:signal({role:'ADMIN',dashboard_path:'/dashboard/admin'})}}]});http=TestBed.inject(HttpTestingController);});
 afterEach(()=>http.verify());
 function open(tipos:any[]=[tipo]){const f=TestBed.createComponent(FactoresComponent);f.detectChanges();http.expectOne(url).flush({trabajador:'Ana',registros:[]});http.expectOne(cat).flush(tipos);f.detectChanges();return f;}
 it('catálogo vacío informa y no presenta formulario',()=>{const f=open([]);expect(f.nativeElement.querySelector('form')).toBeNull();expect(f.nativeElement.textContent).toContain('No hay tipos de factores activos');});
 it('registra propio con tipo configurado y no duplica envíos',()=>{const f=open(),vm=f.componentInstance.vm;vm.tipo='t';vm.nivel='Leve';vm.descripcion='Contexto';vm.guardar();vm.guardar();const r=http.expectOne(url);expect(r.request.body).toEqual({tipo_id:'t',nivel:'Leve',descripcion:'Contexto'});r.flush({id:'r',tipo:'Tipo institucional',fecha:'2026-10-16T12:00:00Z',nivel:'Leve',descripcion:'Contexto'});f.detectChanges();expect(f.nativeElement.textContent).toContain('Contexto');expect(vm.tipo).toBe('');});
 it('tipo desactivado conserva datos del formulario ante error',()=>{const f=open(),vm=f.componentInstance.vm;vm.tipo='t';vm.nivel='Leve';vm.descripcion='Contexto';vm.guardar();http.expectOne(url).flush({detail:'Tipo ya no disponible'}, {status:400,statusText:'Invalid'});expect(vm.descripcion).toBe('Contexto');expect(vm.error()).toBe('Tipo ya no disponible');});
 it('consulta profesional no carga catálogo ni permite escribir',()=>{params.next(convertToParamMap({trabajadorId:'w'}));const f=TestBed.createComponent(FactoresComponent);f.detectChanges();http.expectOne('/api/psicologo/trabajadores/w/factores/').flush({trabajador:'Ana',registros:[]});http.expectNone(cat);f.detectChanges();expect(f.nativeElement.querySelector('form')).toBeNull();f.componentInstance.vm.guardar();http.expectNone(url);});
 it('administración crea y desactiva tipos sin consultar registros privados',()=>{const f=TestBed.createComponent(CatalogoFactoresComponent);f.detectChanges();http.expectOne(cat).flush([]);const vm=f.componentInstance.vm;vm.nombre='Tipo institucional';vm.guardar();http.expectOne(cat).flush(tipo);expect(vm.tipos().length).toBe(1);vm.editar(tipo);vm.activo=false;vm.guardar();const r=http.expectOne(cat+'t/');expect(r.request.method).toBe('PUT');expect(r.request.body.activo).toBe(false);r.flush({...tipo,activo:false});expect(vm.tipos()[0].activo).toBe(false);http.expectNone(url);});
});
