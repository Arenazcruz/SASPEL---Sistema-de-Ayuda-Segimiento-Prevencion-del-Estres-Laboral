import {TestBed} from '@angular/core/testing';
import {signal} from '@angular/core';
import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting,HttpTestingController} from '@angular/common/http/testing';
import {ActivatedRoute,convertToParamMap,provideRouter} from '@angular/router';
import {API_URL} from '../core/auth/api-url';
import {AuthService} from '../core/auth/auth.service';
import {AsignacionesInstrumentoComponent} from './instrumentos/asignaciones';
import {EvolucionComponent} from './evolucion/evolucion';
import {RecomendacionesComponent} from './recomendaciones/recomendaciones';
import {GobiernoComponent} from './gobierno/gobierno';
import {PerfilComponent} from './perfil/perfil';
import {Citas} from './citas/citas';

describe('Flujos de cierre funcional H4',()=>{
 let http:HttpTestingController;
 const route={snapshot:{paramMap:convertToParamMap({}),data:{} as Record<string,string>}};
 const user=signal<any>({role:'TRABAJADOR',dashboard_path:'/dashboard/trabajador'});
 beforeEach(()=>{route.snapshot={paramMap:convertToParamMap({}),data:{}};user.set({role:'TRABAJADOR',dashboard_path:'/dashboard/trabajador'});TestBed.configureTestingModule({providers:[provideHttpClient(),provideHttpClientTesting(),provideRouter([]),{provide:API_URL,useValue:'/api'},{provide:ActivatedRoute,useValue:route},{provide:AuthService,useValue:{user}}]});http=TestBed.inject(HttpTestingController);});
 afterEach(()=>http.verify());

 it('muestra vacío de instrumentos sin ofrecer asignaciones al trabajador',()=>{
  const f=TestBed.createComponent(AsignacionesInstrumentoComponent);f.detectChanges();http.expectOne('/api/trabajador/instrumentos/').flush({asignaciones:[]});f.detectChanges();expect(f.nativeElement.textContent).toContain('No hay instrumentos asignados');expect(f.nativeElement.querySelector('form')).toBeNull();
 });
 it('asigna, bloquea doble envío y conserva el formulario ante error',()=>{
  route.snapshot.paramMap=convertToParamMap({trabajadorId:'w'});const f=TestBed.createComponent(AsignacionesInstrumentoComponent),vm=f.componentInstance.vm;
  http.expectOne('/api/psicologo/trabajadores/w/instrumentos/').flush({asignaciones:[],instrumentos:[{id:'i',nombre:'Prueba',version:'1'}]});
  vm.asignar();expect(vm.error()).toContain('Selecciona');vm.instrumento='i';vm.asignar();vm.asignar();const req=http.expectOne('/api/psicologo/trabajadores/w/instrumentos/');expect(req.request.body).toEqual({instrumento_id:'i',fecha_limite:null});req.flush({detail:'Ya existe'},{status:400,statusText:'Bad Request'});expect(vm.instrumento).toBe('i');expect(vm.error()).toBe('Ya existe');expect(vm.busy()).toBe(false);
 });
 it('refresca instrumentos después de asignar',()=>{
  route.snapshot.paramMap=convertToParamMap({trabajadorId:'w'});const f=TestBed.createComponent(AsignacionesInstrumentoComponent),vm=f.componentInstance.vm;
  http.expectOne('/api/psicologo/trabajadores/w/instrumentos/').flush({asignaciones:[],instrumentos:[]});vm.instrumento='i';vm.asignar();http.expectOne('/api/psicologo/trabajadores/w/instrumentos/').flush({id:'a'});expect(vm.busy()).toBe(true);http.expectOne('/api/psicologo/trabajadores/w/instrumentos/').flush({asignaciones:[],instrumentos:[]});expect(vm.instrumento).toBe('');expect(vm.mensaje()).toContain('asignado');
 });
 it('evolución conserva versiones separadas y fechas filtradas',()=>{
  const f=TestBed.createComponent(EvolucionComponent),vm=f.componentInstance.vm;http.expectOne('/api/trabajador/evolucion/').flush({series:[]});f.detectChanges();expect(f.nativeElement.textContent).toContain('No hay evaluaciones');vm.desde='2026-01-01';vm.hasta='2026-01-31';vm.load();http.expectOne('/api/trabajador/evolucion/?desde=2026-01-01&hasta=2026-01-31').flush({series:[]});vm.hasta='2025-01-01';vm.load();expect(vm.error()).toContain('orden');
 });
 it('evolución no muestra historial anterior al perder permisos',()=>{
  route.snapshot.paramMap=convertToParamMap({trabajadorId:'w'});const vm=TestBed.createComponent(EvolucionComponent).componentInstance.vm;const url='/api/psicologo/trabajadores/w/evolucion/';http.expectOne(url).flush({series:[]});vm.load();http.expectOne(url).flush({detail:'No autorizado'},{status:403,statusText:'Forbidden'});expect(vm.datos()).toBeNull();expect(vm.error()).not.toBe('');
 });
 it('recomendación se asocia al seguimiento y admite transición',()=>{
  route.snapshot.paramMap=convertToParamMap({seguimientoId:'s'});const vm=TestBed.createComponent(RecomendacionesComponent).componentInstance.vm;const url='/api/seguimientos/s/recomendaciones/';http.expectOne(url).flush([]);vm.texto='Acción manual';vm.guardar();const r=http.expectOne(url);expect(r.request.body).toEqual({texto:'Acción manual',compartida:false});r.flush({id:'r'});http.expectOne(url).flush([{id:'r',estado:'PENDIENTE',texto:'Acción manual'}]);vm.cambiar(vm.datos()![0],'COMPLETADA');http.expectOne(url+'r/estado/').flush({id:'r'});http.expectOne(url).flush([{id:'r',estado:'COMPLETADA'}]);expect(vm.datos()![0].estado).toBe('COMPLETADA');
 });
 it('recomendaciones preservan texto ante un fallo y evitan envío vacío',()=>{
  route.snapshot.paramMap=convertToParamMap({seguimientoId:'s'});const vm=TestBed.createComponent(RecomendacionesComponent).componentInstance.vm;const url='/api/seguimientos/s/recomendaciones/';http.expectOne(url).flush([]);vm.guardar();expect(vm.error()).toContain('Escribe');vm.texto='Borrador';vm.guardar();http.expectOne(url).flush({detail:'Interno secreto'},{status:500,statusText:'Error'});expect(vm.texto).toBe('Borrador');expect(vm.error()).not.toContain('secreto');
 });
 it('políticas requieren confirmación y no reescriben la versión existente',()=>{
  route.snapshot.data={modo:'politicas'};const vm=TestBed.createComponent(GobiernoComponent).componentInstance.vm;http.expectOne('/api/administracion/politicas/').flush([]);vm.form={tipo:'TERMINOS_USO',titulo:'Prueba',version:'2',contenido:'Texto sintético',obligatoria:true};vm.publicar();expect(vm.error()).toContain('confirma');vm.confirmacion=true;vm.publicar();const r=http.expectOne('/api/administracion/politicas/');expect(r.request.method).toBe('POST');expect(r.request.body.version).toBe('2');r.flush({});http.expectOne('/api/administracion/politicas/').flush([]);expect(vm.mensaje()).toContain('nueva aceptación');
 });
 it('auditoría pagina y limpia resultados al fallar',()=>{
  route.snapshot.data={modo:'auditoria'};const vm=TestBed.createComponent(GobiernoComponent).componentInstance.vm;http.expectOne('/api/administracion/auditoria/?page=1').flush({count:51,page:1,page_size:50,results:[]});vm.pagina(1);http.expectOne('/api/administracion/auditoria/?page=2').flush({detail:'No autorizado'},{status:403,statusText:'Forbidden'});expect(vm.eventos()).toBeNull();
 });
 it('perfil solo envía campos personales permitidos',()=>{
  const vm=TestBed.createComponent(PerfilComponent).componentInstance.vm;
  http.expectOne('/api/perfil/').flush({first_name:'Ana',last_name:'Prueba',apellido_materno:'',telefono:'',fecha_nacimiento:null,sexo:'',email:'sintetico@saspel.com',codigo_empleado:'DEMO',area:'Área',cargo:'Cargo'});vm.form.telefono='71234567';vm.guardar();const r=http.expectOne('/api/perfil/');expect(r.request.method).toBe('PATCH');expect(r.request.body.codigo_empleado).toBeUndefined();expect(r.request.body.email).toBeUndefined();r.flush({detail:'Validación'},{status:400,statusText:'Bad Request'});expect(vm.form.telefono).toBe('71234567');
 });
 it('reprogramación valida y envía solo horario y motivo',()=>{
  user.set({role:'PSICOLOGO',dashboard_path:'/dashboard/psicologo'});const vm=TestBed.createComponent(Citas).componentInstance.vm;http.expectOne('/api/citas/').flush([]);http.expectOne('/api/psicologo/disponibilidad/').flush([]);const cita={id:'c'} as any;vm.reprogramar(cita);expect(vm.error()).toContain('horario');vm.nuevosInicios['c']='2099-01-01T10:00';vm.nuevosFines['c']='2099-01-01T11:00';vm.cierres['c']='Cambio';vm.reprogramar(cita);vm.reprogramar(cita);const r=http.expectOne('/api/citas/c/reprogramar/');expect(r.request.body.motivo).toBe('Cambio');expect(r.request.body.trabajador_id).toBeUndefined();r.flush({detail:'Horario ocupado'},{status:400,statusText:'Bad Request'});expect(vm.nuevosInicios['c']).toBe('2099-01-01T10:00');expect(vm.error()).toBe('Horario ocupado');
 });
 it('el trabajador consulta sus acciones compartidas sin controles profesionales',()=>{
  const f=TestBed.createComponent(RecomendacionesComponent);
  http.expectOne('/api/trabajador/recomendaciones/').flush([{id:'r',texto:'Acción de ejemplo',estado:'PENDIENTE'}]);
  f.detectChanges();
  expect(f.nativeElement.textContent).toContain('Acción de ejemplo');
  expect(f.nativeElement.querySelector('form')).toBeNull();
  expect(f.nativeElement.textContent).not.toContain('Completar');
 });});
