/**
 * Ilustración decorativa de bienvenida hecha con elementos de plantilla y SCSS. Revisar
 * welcome-art.scss para formas y distribución; no contiene acciones ni consultas.
 */
import { Component } from '@angular/core';

@Component({
  selector: 'app-welcome-art',
  template: `<div
    class="hero-art"
    aria-label="Ilustración de crecimiento y bienestar compartido"
    role="img"
  >
    <div class="art-grid"></div>
    <div class="orbit orbit-one"></div>
    <div class="orbit orbit-two"></div>
    <div class="art-word">Cuidar de ti.<br /><em>Crecer en equipo.</em></div>
    <div class="growth">
      <span class="stem"></span><span class="leaf leaf-one"></span
      ><span class="leaf leaf-two"></span><span class="leaf leaf-three"></span
      ><span class="leaf leaf-four"></span><span class="seed"></span>
    </div>
    <span class="art-pill"><span aria-hidden="true">✦</span> Personas primero</span>
    <div class="art-footer"><span>SASPEL / 2026</span><span>CRECER IFD ↗</span></div>
  </div>`,
  styleUrl: './welcome-art.scss',
})
export class WelcomeArt {}
