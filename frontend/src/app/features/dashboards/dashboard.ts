/**
 * Panel compartido de bienvenida de roles distintos de Superadmin. Muestra identidad y texto
 * de DashboardViewModel y permite cerrar sesión. Las herramientas futuras no cargan datos
 * aquí; Superadmin tiene pantalla propia en features/superadmin/dashboard.
 */
import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Brand } from '../../shared/brand/brand';
import { DashboardViewModel } from './dashboard.viewmodel';

@Component({
  selector: 'app-dashboard',
  imports: [RouterLink, Brand],
  providers: [DashboardViewModel],
  template: `
    <header class="dashboard-header wrap">
      <a routerLink="/" aria-label="SASPEL, inicio"><app-brand /></a>
      <div class="session-actions">
        <span>{{ vm.user()?.email }}</span
        ><button class="button button-outline button-small" (click)="vm.logout()">
          Cerrar sesión ↗
        </button>
      </div>
    </header>
    <main class="wrap dashboard-main">
      <p class="eyebrow">SASPEL / {{ vm.panel()?.label }}</p>
      <h1>{{ vm.panel()?.title }}</h1>
      <section class="welcome-panel">
        <span class="panel-symbol" aria-hidden="true">✳</span>
        <p class="eyebrow">BIENVENIDO A SASPEL</p>
        <h2>Hola, {{ vm.displayName() }}.</h2>
        <p>{{ vm.panel()?.description }}</p>
        <span class="role-label">{{ vm.panel()?.label }}</span>
        <div class="panel-note">
          Tu sesión está activa. Este es el espacio inicial de tu cuenta; las funciones de este
          panel estarán disponibles más adelante.
        </div>
      </section>
    </main>
    <footer class="wrap dashboard-footer">CRECER IFD · Proyecto académico 2026</footer>
  `,
  styles: [
    `
      :host {
        display: flex;
        flex-direction: column;
        min-height: 100dvh;
      }
      .dashboard-header {
        height: 110px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 25px;
      }
      .session-actions {
        display: flex;
        align-items: center;
        gap: 25px;
        font-size: 12px;
        color: var(--muted);
      }
      .dashboard-main {
        flex: 1;
        padding-top: 55px;
        padding-bottom: 50px;
      }
      h1 {
        font-size: clamp(28px, 4vw, 45px);
        letter-spacing: -1.5px;
        line-height: 1.2;
        margin: 18px 0 40px;
      }
      .welcome-panel {
        background: #edf2e9;
        border: 1px solid #d9e3d6;
        padding: 50px;
        border-radius: 14px;
        max-width: 950px;
      }
      .panel-symbol {
        font-size: 48px;
        color: var(--green);
        display: block;
        margin-bottom: 25px;
      }
      .welcome-panel h2 {
        overflow-wrap: anywhere;
        font-size: 30px;
      }
      .welcome-panel > p:not(.eyebrow) {
        font-size: 16px;
        line-height: 1.9;
        max-width: 650px;
        color: var(--muted);
      }
      .role-label {
        display: inline-block;
        font-size: 11px;
        padding: 7px 12px;
        background: white;
        border-radius: 5px;
        margin: 15px 0;
      }
      .panel-note {
        border-top: 1px solid #cad8c7;
        padding-top: 22px;
        margin-top: 15px;
        font-size: 12px;
        line-height: 1.8;
        color: var(--muted);
        max-width: 680px;
      }
      .dashboard-footer {
        padding-bottom: 30px;
        font-size: 11px;
        color: var(--muted);
      }
      @media (max-width: 650px) {
        .dashboard-header {
          height: auto;
          padding-top: 25px;
          padding-bottom: 25px;
          align-items: start;
        }
        .session-actions {
          flex-direction: column;
          align-items: end;
          gap: 10px;
        }
        .session-actions > span {
          max-width: 160px;
          overflow-wrap: anywhere;
          font-size: 10px;
        }
        .dashboard-main {
          padding-top: 25px;
        }
        .welcome-panel {
          padding: 26px;
        }
        .welcome-panel h2 {
          font-size: 25px;
        }
      }
    `,
  ],
})
export class Dashboard {
  readonly vm = inject(DashboardViewModel);
}
