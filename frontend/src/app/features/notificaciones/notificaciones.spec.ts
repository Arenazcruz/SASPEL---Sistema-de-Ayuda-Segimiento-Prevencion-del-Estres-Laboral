import {TestBed} from '@angular/core/testing';
import {signal} from '@angular/core';
import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting,HttpTestingController} from '@angular/common/http/testing';
import {provideRouter} from '@angular/router';
import {AuthService} from '../../core/auth/auth.service';
import {API_URL} from '../../core/auth/api-url';
import {NotificacionesComponent} from './notificaciones';
describe('Centro de notificaciones',()=>{
 let http:HttpTestingController;const user=signal<any>({role:'TRABAJADOR'});
 beforeEach(()=>{user.set({role:'TRABAJADOR'});TestBed.configureTestingModule({providers:[provideHttpClient(),provideHttpClientTesting(),provideRouter([]),{provide:API_URL,useValue:'/api'},{provide:AuthService,useValue:{user}}]});http=TestBed.inject(HttpTestingController);});
 afterEach(()=>http.verify());
 function open(){const f=TestBed.createComponent(NotificacionesComponent);f.detectChanges();return f;}
 it('carga, vacío y error recuperable',()=>{const f=open();expect(f.nativeElement.textContent).toContain('Consultando');http.expectOne('/api/notificaciones/?pendientes=false').flush([]);f.detectChanges();expect(f.nativeElement.textContent).toContain('No hay notificaciones');f.componentInstance.vm.load();http.expectOne('/api/notificaciones/?pendientes=false').flush({}, {status:500,statusText:'Error'});expect(f.componentInstance.vm.datos()).toBeNull();expect(f.componentInstance.vm.error()).toBeTruthy();});
 it('marca lectura sin suplantar y evita doble envío',()=>{const f=open(),vm=f.componentInstance.vm;const row={id:'n',titulo:'Cita actualizada',tipo:'CITA',origen_id:'o',creado_en:'2026-10-16',leida_en:null};http.expectOne('/api/notificaciones/?pendientes=false').flush([row]);vm.leer(row);vm.leer(row);const r=http.expectOne('/api/notificaciones/n/leer/');expect(r.request.body).toEqual({});r.flush({id:'n',leida_en:'2026-10-16'});expect(vm.datos()?.[0].leida_en).toBeTruthy();});
 it('atención profesional y revocación retira alertas',()=>{user.set({role:'PSICOLOGO'});const f=open(),vm=f.componentInstance.vm;http.expectOne('/api/notificaciones/?pendientes=false').flush([]);const row:any={id:'a',estado:'ABIERTA',acciones:[]};http.expectOne('/api/alertas/').flush([row]);vm.actuar(row,'CERRADA','Revisada');const r=http.expectOne('/api/alertas/a/acciones/');expect(r.request.body).toEqual({estado:'CERRADA',observacion:'Revisada'});r.flush({}, {status:404,statusText:'Not Found'});expect(vm.alertas()).toBeNull();});
});
