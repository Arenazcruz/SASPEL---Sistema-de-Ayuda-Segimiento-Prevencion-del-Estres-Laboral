import {HttpErrorResponse} from '@angular/common/http';
import {apiError} from './superadmin.service';

describe('Mensajes seguros de errores API', () => {
  it('extrae validaciones anidadas sin objetos ni metadatos técnicos', () => {
    const error = new HttpErrorResponse({status:400,error:{respuestas:[{opcion_id:['Selecciona una opción válida.']}],code:'invalid_internal'}});
    expect(apiError(error)).toBe('Selecciona una opción válida.');
  });
  it('no muestra códigos JWT ni detalles técnicos del servidor', () => {
    expect(apiError(new HttpErrorResponse({status:401,error:{code:'token_not_valid',messages:[{token_class:'AccessToken'}]}}))).toContain('sesión');
    expect(apiError(new HttpErrorResponse({status:500,error:{detail:'Traceback SQL SELECT secreto'}}))).not.toContain('secreto');
  });
  it('usa un mensaje comprensible para cuerpos vacíos o no válidos', () => {
    for (const body of [null, {}, {field:{unexpected:123}}, '<html>Error</html>']) {
      expect(apiError(new HttpErrorResponse({status:400,error:body}))).toBe('No se pudo completar la operación.');
    }
  });
});
