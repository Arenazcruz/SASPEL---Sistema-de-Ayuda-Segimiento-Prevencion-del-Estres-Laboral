/**
 * Prueba el formulario y su ViewModel: validación, mensajes y navegación mediante AuthService
 * simulado. Conserva comprobaciones de limpieza de clave y de envíos repetidos.
 */
import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, Subject, throwError } from 'rxjs';
import { AuthService } from '../../../core/auth/auth.service';
import { AuthUser } from '../../../core/auth/auth.models';
import { LoginComponent } from './login';

describe('LoginComponent', () => {
  const user: AuthUser = {
    id: 1,
    email: 'test@saspel.com',
    first_name: '',
    last_name: '',
    role: 'SUPERADMIN',
    dashboard_path: '/dashboard/superadmin',
  };
  let login: ReturnType<typeof vi.fn>;
  beforeEach(() => {
    login = vi.fn().mockReturnValue(of(user));
    TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [provideRouter([]), { provide: AuthService, useValue: { login } }],
    });
  });

  it('muestra validaciones sin enviar credenciales incompletas', async () => {
    const fixture = TestBed.createComponent(LoginComponent);
    fixture.componentInstance.vm.submit();
    await fixture.whenStable();
    expect(login).not.toHaveBeenCalled();
    expect(fixture.nativeElement.textContent).toContain('Ingresa un correo electrónico válido.');
  });

  it('permite mostrar y ocultar la contraseña', async () => {
    const fixture = TestBed.createComponent(LoginComponent);
    await fixture.whenStable();
    const input = fixture.nativeElement.querySelector('#password') as HTMLInputElement;
    expect(input.type).toBe('password');
    fixture.nativeElement.querySelector('.password-toggle').click();
    await fixture.whenStable();
    expect(input.type).toBe('text');
  });

  it('envía los datos, borra la contraseña del formulario y abre el panel', () => {
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    const fixture = TestBed.createComponent(LoginComponent);
    fixture.componentInstance.vm.form.setValue({
      email: 'test@SASPEL.COM',
      password: 'test-secret',
    });
    fixture.componentInstance.vm.submit();
    expect(login).toHaveBeenCalledWith('test@SASPEL.COM', 'test-secret');
    expect(navigate).toHaveBeenCalledWith('/dashboard/superadmin');
    expect(fixture.componentInstance.vm.form.controls.password.value).toBe('');
  });

  it('muestra un error genérico cuando las credenciales son incorrectas', async () => {
    login.mockReturnValue(throwError(() => new HttpErrorResponse({ status: 401 })));
    const fixture = TestBed.createComponent(LoginComponent);
    fixture.componentInstance.vm.form.setValue({
      email: 'test@saspel.com',
      password: 'incorrecta',
    });
    fixture.componentInstance.vm.submit();
    await fixture.whenStable();
    expect(fixture.nativeElement.querySelector('[role=alert]').textContent).toContain(
      'Credenciales no válidas.',
    );
    expect(fixture.componentInstance.vm.loading()).toBe(false);
  });

  // Dejamos la respuesta pendiente para simular dos intentos mientras el servidor contesta.
  it('bloquea envíos repetidos mientras espera una respuesta', async () => {
    const response = new Subject<AuthUser>();
    login.mockReturnValue(response);
    const fixture = TestBed.createComponent(LoginComponent);
    fixture.componentInstance.vm.form.setValue({
      email: 'test@saspel.com',
      password: 'test-secret',
    });
    fixture.componentInstance.vm.submit();
    fixture.componentInstance.vm.submit();
    await fixture.whenStable();
    expect(login).toHaveBeenCalledTimes(1);
    expect(fixture.nativeElement.querySelector('[type=submit]').disabled).toBe(true);
    response.complete();
  });

  it('rechaza dominios externos y sufijos engañosos con un mensaje genérico', async () => {
    const fixture = TestBed.createComponent(LoginComponent);
    for (const email of [
      'test@example.com',
      'test@saspel.com.evil.com',
      'test@sub.saspel.com',
      'test@falsosaspel.com',
    ]) {
      fixture.componentInstance.vm.form.setValue({ email, password: 'test-secret' });
      fixture.componentInstance.vm.submit();
      await fixture.whenStable();
      expect(login).not.toHaveBeenCalled();
      expect(fixture.nativeElement.querySelector('#email-error').textContent).toContain(
        'Credenciales no válidas.',
      );
    }
  });

  it('conserva el mensaje de cuenta inactiva enviado por backend', async () => {
    login.mockReturnValue(
      throwError(
        () =>
          new HttpErrorResponse({
            status: 403,
            error: { detail: 'Esta cuenta no está habilitada para ingresar.' },
          }),
      ),
    );
    const fixture = TestBed.createComponent(LoginComponent);
    fixture.componentInstance.vm.form.setValue({
      email: 'test@saspel.com',
      password: 'test-secret',
    });
    fixture.componentInstance.vm.submit();
    await fixture.whenStable();
    expect(fixture.nativeElement.querySelector('[role=alert]').textContent).toContain(
      'Esta cuenta no está habilitada para ingresar.',
    );
  });
});
