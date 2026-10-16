import {TestBed} from '@angular/core/testing';
import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting,HttpTestingController} from '@angular/common/http/testing';
import {ActivatedRoute,convertToParamMap,provideRouter} from '@angular/router';
import {BehaviorSubject} from 'rxjs';
import {API_URL} from '../../core/auth/api-url';
import {AnimoComponent} from './animo';
describe('Estado de ánimo',()=>{
 let http:HttpTestingController;let params:BehaviorSubject<any>;const url='/api/trabajador/animo/';
 beforeEach(()=>{params=new BehaviorSubject(convertToParamMap({}));TestBed.configureTestingModule({providers:[provideHttpClient(),provideHttpClientTesting(),provideRouter([]),{provide:API_URL,useValue:'/api'},{provide:ActivatedRoute,useValue:{paramMap:params}}]});http=TestBed.inject(HttpTestingController);});
 afterEach(()=>http.verify());
 function open(path=url){const f=TestBed.createComponent(AnimoComponent);f.detectChanges();http.expectOne(path).flush({trabajador:'Ana',registros:[]});f.detectChanges();return f;}
 it('registro propio, sin suplantación y evita doble envío',()=>{const f=open(),vm=f.componentInstance.vm;vm.estado='Tranquila';vm.intensidad='Leve';vm.guardar();vm.guardar();const r=http.expectOne(url);expect(r.request.body).toEqual({estado:'Tranquila',intensidad:'Leve',comentario:''});r.flush({id:'r',fecha:'2026-10-16T12:00:00Z',estado:'Tranquila',intensidad:'Leve',comentario:''});f.detectChanges();expect(f.nativeElement.textContent).toContain('Tranquila');expect(vm.estado).toBe('');});
 it('profesional consulta sin formulario y cambio de ruta no conserva historial',()=>{params.next(convertToParamMap({trabajadorId:'w'}));const f=open('/api/psicologo/trabajadores/w/animo/');expect(f.nativeElement.querySelector('form')).toBeNull();f.componentInstance.vm.guardar();http.expectNone(url);params.next(convertToParamMap({trabajadorId:'otro'}));http.expectOne('/api/psicologo/trabajadores/otro/animo/').flush({}, {status:404,statusText:'Not Found'});expect(f.componentInstance.vm.datos()).toBeNull();});
 it('valida y conserva texto ante error',()=>{const f=open(),vm=f.componentInstance.vm;vm.guardar();http.expectNone(url);vm.estado='Serena';vm.intensidad='Media';vm.guardar();http.expectOne(url).flush({}, {status:400,statusText:'Invalid'});expect(vm.estado).toBe('Serena');expect(vm.busy()).toBe(false);});
});
