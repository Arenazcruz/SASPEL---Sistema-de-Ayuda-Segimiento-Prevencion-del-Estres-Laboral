/**
 * Carga persona por ID de ruta y coordina cambio de rol/estado mediante SuperadminService.
 * Expone avisos, carga y operación en curso; las restricciones definitivas están en permisos y
 * casos de uso del backend.
 */
import { DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';
import { finalize } from 'rxjs';
import { AuthService } from '../../../core/auth/auth.service';
import { CREATION_ROLES, Person } from '../superadmin.models';
import { apiError, SuperadminService } from '../superadmin.service';

@Injectable()
export class UserDetailViewModel {
  private readonly api = inject(SuperadminService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly route = inject(ActivatedRoute);
  readonly id = Number(this.route.snapshot.paramMap.get('id'));
  readonly currentUser = inject(AuthService).user;
  readonly person = signal<Person | null>(null);
  readonly loading = signal(false);
  readonly busy = signal(false);
  readonly error = signal('');
  readonly notice = signal(
    this.route.snapshot.queryParamMap.has('saved') ? 'Datos guardados correctamente.' : '',
  );
  readonly selectedRole = signal('');
  readonly roles = CREATION_ROLES;
  constructor() {
    this.load();
  }
  /**
   * Consulta persona por ID y actualiza ficha y rol seleccionado; muestra fallo sin cambiar
   * datos del servidor.
   */
  load() {
    this.loading.set(true);
    this.error.set('');
    this.api
      .user(this.id)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (person) => {
          this.person.set(person);
          this.selectedRole.set(person.role || '');
        },
        error: (e) => this.error.set(apiError(e)),
      });
  }
  /**
   * Devuelve si la UI ofrece corrección desde rol administrativo y no es la propia cuenta; el
   * backend vuelve a validar cada petición.
   */
  canChangeRole() {
    return (
      ['PSICOLOGO', 'ADMIN', 'SUPERADMIN'].includes(this.person()?.role || '') &&
      this.id !== this.currentUser()?.id
    );
  }
  /**
   * Confirma activación/desactivación de la ficha y delega a run la suscripción y mensajes.
   */
  toggle() {
    const user = this.person();
    if (
      !user ||
      this.busy() ||
      !window.confirm(`${user.is_active ? 'Desactivar' : 'Activar'} a ${user.email}?`)
    )
      return;
    this.run(
      this.api.active(this.id, !user.is_active),
      user.is_active ? 'Usuario desactivado.' : 'Usuario activado.',
    );
  }
  /**
   * Confirma el rol elegido, con aviso adicional para SUPERADMIN, y envía la acción mediante
   * run.
   */
  changeRole() {
    if (this.busy() || !this.selectedRole()) return;
    const warning =
      this.selectedRole() === 'SUPERADMIN'
        ? ' Este rol posee administración global del sistema.'
        : '';
    if (!window.confirm(`¿Confirmas cambiar el rol de ${this.person()?.email}?${warning}`)) return;
    this.run(this.api.role(this.id, this.selectedRole()), 'Rol actualizado.');
  }
  /**
   * Recibe observable de persona y mensaje de éxito; serializa la acción con busy y actualiza
   * ficha, rol y avisos. Los errores HTTP se convierten con apiError.
   */
  private run(request: ReturnType<SuperadminService['user']>, message: string) {
    this.busy.set(true);
    this.error.set('');
    this.notice.set('');
    request
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.busy.set(false)),
      )
      .subscribe({
        next: (person) => {
          this.person.set(person);
          this.selectedRole.set(person.role || '');
          this.notice.set(message);
        },
        error: (e) => this.error.set(apiError(e)),
      });
  }
}
