/**
 * Marca reutilizable de SASPEL para bienvenida, login y paneles. Plantilla y estilos se
 * definen en este componente; no depende de sesión ni realiza HTTP.
 */
import { Component } from '@angular/core';

@Component({
  selector: 'app-brand',
  template: `<span class="brand"
    ><span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i><i></i></span
    ><span>SASPEL<span class="brand-caption">BIENESTAR QUE NOS UNE</span></span></span
  >`,
  styles: [
    `
      :host {
        display: inline-block;
      }
      .brand {
        display: flex;
        gap: 12px;
        align-items: center;
        font-size: 25px;
        font-weight: 800;
        letter-spacing: 1px;
      }
      .brand-caption {
        display: block;
        font-size: 8px;
        letter-spacing: 1.65px;
        margin-top: 3px;
        font-weight: 600;
      }
      .brand-mark {
        display: grid;
        grid-template-columns: 12px 12px;
        gap: 3px;
        transform: rotate(-10deg);
      }
      i {
        height: 12px;
        background: currentColor;
        border-radius: 8px 8px 2px 8px;
      }
      i:nth-child(2) {
        opacity: 0.4;
        transform: rotate(90deg);
      }
      i:nth-child(3) {
        opacity: 0.6;
        transform: rotate(-90deg);
      }
      i:nth-child(4) {
        transform: rotate(180deg);
      }
    `,
  ],
})
export class Brand {}
