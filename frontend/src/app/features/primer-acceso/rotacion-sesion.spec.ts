import {provideHttpClient} from '@angular/common/http';
import {HttpTestingController,provideHttpClientTesting} from '@angular/common/http/testing';
import {TestBed} from '@angular/core/testing';
import {API_URL} from '../../core/auth/api-url';
import {TokenStorageService} from '../../core/auth/token-storage.service';
import {PrimerAccesoService} from './primer-acceso.service';

describe('Rotación tras cambiar contraseña',()=>{
 beforeEach(()=>TestBed.configureTestingModule({providers:[provideHttpClient(),provideHttpClientTesting(),{provide:API_URL,useValue:'/api'}]}));
 afterEach(()=>{TestBed.inject(HttpTestingController).verify();TestBed.inject(TokenStorageService).clear();});
 for(const cerrar of [false,true]){
  it(cerrar?'no restaura una sesión cerrada durante la petición':'reemplaza ambos tokens revocados para continuar el primer acceso',()=>{
   const storage=TestBed.inject(TokenStorageService);storage.save({access:'anterior',refresh:'anterior-refresh'});
   TestBed.inject(PrimerAccesoService).cambiarPassword({password:'Nueva-582!',password_confirmation:'Nueva-582!'}).subscribe();
   if(cerrar)storage.clear();
   TestBed.inject(HttpTestingController).expectOne('/api/auth/primer-acceso/password/').flush({tokens:{access:'nuevo',refresh:'nuevo-refresh'}});
   expect(storage.access).toBe(cerrar?null:'nuevo');expect(storage.refresh).toBe(cerrar?null:'nuevo-refresh');
  });
 }
});
