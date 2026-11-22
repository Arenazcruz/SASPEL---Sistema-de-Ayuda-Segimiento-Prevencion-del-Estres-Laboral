import {TestBed} from '@angular/core/testing';
import {signal} from '@angular/core';
import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting,HttpTestingController} from '@angular/common/http/testing';
import {provideRouter} from '@angular/router';
import {AuthService} from '../../core/auth/auth.service';
import {API_URL} from '../../core/auth/api-url';
import {ReportesComponent} from './reportes';
import {ReportesService} from './reportes.service';
describe('Reportes operativos',()=>{
 let http:HttpTestingController;
 beforeEach(()=>{TestBed.configureTestingModule({providers:[provideHttpClient(),provideHttpClientTesting(),provideRouter([]),{provide:API_URL,useValue:'/api'},{provide:AuthService,useValue:{user:signal({role:'ADMIN'})}}]});http=TestBed.inject(HttpTestingController);});
 afterEach(()=>http.verify());
 function open(){const f=TestBed.createComponent(ReportesComponent);f.detectChanges();http.expectOne('/api/reportes/catalogos/').flush({areas:[],instrumentos:[]});http.expectOne('/api/reportes/usuarios/?pagina=1').flush({tipo:'usuarios',columnas:['Nombre'],filas:[],total:0,pagina:1,por_pagina:50,agregado:false});return f;}
 it('vacío y filtros principales',()=>{const f=open();f.detectChanges();expect(f.nativeElement.textContent).toContain('No hay registros');const vm=f.componentInstance.vm;vm.tipo='citas';vm.desde='2026-10-01';vm.hasta='2026-10-24';vm.estado='CONFIRMADA';vm.buscar();http.expectOne('/api/reportes/citas/?pagina=1&desde=2026-10-01&hasta=2026-10-24&estado=CONFIRMADA').flush({columnas:['Cantidad'],filas:[[3]],total:1,pagina:1,por_pagina:50,agregado:true});f.detectChanges();expect(f.nativeElement.textContent).toContain('Reporte agregado');});
 it('exporta con el mismo filtro y controla doble envío',()=>{const f=open(),vm=f.componentInstance.vm;const download=vi.spyOn(TestBed.inject(ReportesService),'descargar').mockImplementation(()=>{});vm.exportar();vm.exportar();const r=http.expectOne('/api/reportes/usuarios/?pagina=1&formato=csv');expect(r.request.responseType).toBe('blob');r.flush(new Blob(['Nombre\nPrueba']));expect(download).toHaveBeenCalledOnce();});
 it('revocación limpia resultados y fechas inválidas no consultan',()=>{const f=open(),vm=f.componentInstance.vm;vm.load();http.expectOne('/api/reportes/usuarios/?pagina=1').flush({}, {status:403,statusText:'Forbidden'});expect(vm.datos()).toBeNull();vm.desde='2026-10-24';vm.hasta='2026-10-01';vm.load();http.expectNone('/api/reportes/usuarios/?pagina=1');expect(vm.error()).toContain('intervalo');});
});
