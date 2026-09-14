/**
 * Guarda access y refresh en sessionStorage de esta pestaña bajo saspel.access/saspel.refresh.
 * No almacena contraseña ni identidad; si cambia el almacenamiento revisar AuthService y sus
 * pruebas de logout y respuestas tardías.
 */
import { Injectable } from '@angular/core';
import { TokenPair } from './auth.models';

@Injectable({ providedIn: 'root' })
export class TokenStorageService {
  get access(): string | null {
    return sessionStorage.getItem('saspel.access');
  }
  get refresh(): string | null {
    return sessionStorage.getItem('saspel.refresh');
  }
  /**
   * Guarda el par recibido del login en la pestaña; no persiste otros campos de la respuesta.
   */
  save(tokens: TokenPair): void {
    sessionStorage.setItem('saspel.access', tokens.access);
    sessionStorage.setItem('saspel.refresh', tokens.refresh);
  }
  updateAccess(access: string): void {
    sessionStorage.setItem('saspel.access', access);
  }
  /**
   * Elimina solo las dos claves de tokens de SASPEL; AuthService se encarga de limpiar
   * identidad y navegar.
   */
  clear(): void {
    sessionStorage.removeItem('saspel.access');
    sessionStorage.removeItem('saspel.refresh');
  }
}
