import {TestBed} from '@angular/core/testing';
import {signal} from '@angular/core';
import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting,HttpTestingController} from '@angular/common/http/testing';
import {provideRouter} from '@angular/router';
import {AuthService} from '../../core/auth/auth.service';
import {API_URL} from '../../core/auth/api-url';
import {Citas} from './citas';
describe('Citas',()=>{
 let http:HttpTestingController;
 const user=signal<any>({role:'TRABAJADOR',dashboard_path:'/dashboard/trabajador'});
 beforeEach(()=>{user.set({role:'TRABAJADOR',dashboard_path:'/dashboard/trabajador'});TestBed.configureTestingModule({providers:[provideHttpClient(),provideHttpClientTesting(),provideRouter([]),{provide:API_URL,useValue:'/api'},{provide:AuthService,useValue:{user}}]});http=TestBed.inject(HttpTestingController);});
 afterEach(()=>http.verify());
 function abrir(){const f=TestBed.createComponent(Citas);f.detectChanges();http.expectOne('/api/citas/').flush([]);http.expectOne(user().role==='PSICOLOGO'?'/api/psicologo/disponibilidad/':'/api/citas/contexto/').flush(user().role==='PSICOLOGO'?[]:{psicologo:'Profesional',disponibilidad:[{id:'b',dia_semana:0,hora_inicio:'08:00',hora_fin:'18:00'}]});f.detectChanges();return f;}
 it('muestra vacío y valida solicitud sin enviar datos de otro usuario',()=>{const f=abrir(),vm=f.componentInstance.vm;expect(f.nativeElement.textContent).toContain('No tienes citas');vm.solicitar();http.expectNone('/api/citas/');expect(vm.error()).toContain('motivo');vm.inicio='2099-01-01T10:00';vm.fin='2099-01-01T11:00';vm.motivo='Consulta';vm.solicitar();vm.solicitar();const r=http.expectOne('/api/citas/');expect(r.request.body.trabajador_id).toBeUndefined();r.flush({}, {status:400,statusText:'Invalid'});expect(vm.motivo).toBe('Consulta');expect(vm.busy()).toBe(false);});
 it('solicitud exitosa limpia formulario y actualiza historial',()=>{const f=abrir(),vm=f.componentInstance.vm;vm.inicio='2099-01-01T10:00';vm.fin='2099-01-01T11:00';vm.motivo='Consulta';vm.solicitar();http.expectOne('/api/citas/').flush({});http.expectOne('/api/citas/').flush([]);http.expectOne('/api/citas/contexto/').flush({psicologo:'P',disponibilidad:[]});expect(vm.motivo).toBe('');expect(vm.mensaje()).toContain('guardados');});
 it('profesional configura disponibilidad y requiere motivo para rechazar',()=>{user.set({role:'PSICOLOGO',dashboard_path:'/dashboard/psicologo'});const f=abrir(),vm=f.componentInstance.vm;vm.desde='08:00';vm.hasta='12:00';vm.guardarBloque();http.expectOne('/api/psicologo/disponibilidad/').flush([]);http.expectOne('/api/citas/').flush([]);http.expectOne('/api/psicologo/disponibilidad/').flush([]);vm.accion({id:'c'} as any,'rechazar');expect(vm.error()).toContain('motivo');vm.cierres['c']='No disponible';vm.accion({id:'c'} as any,'rechazar');http.expectOne('/api/citas/c/rechazar/').flush({detail:'Cambio concurrente'},{status:400,statusText:'Invalid'});expect(vm.error()).toBe('Cambio concurrente');});
 it('errores de lectura no muestran información anterior',()=>{const f=TestBed.createComponent(Citas);f.detectChanges();http.expectOne('/api/citas/').flush({}, {status:403,statusText:'Forbidden'});http.match('/api/citas/contexto/');expect(f.componentInstance.vm.citas()).toEqual([]);expect(f.componentInstance.vm.ready()).toBe(false);});
});
