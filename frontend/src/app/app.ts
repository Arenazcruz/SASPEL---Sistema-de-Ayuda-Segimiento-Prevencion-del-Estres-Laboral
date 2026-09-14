/**
 * Contenedor raíz de Angular: muestra el RouterOutlet. Las pantallas se eligen en
 * app.routes.ts; este componente no carga datos.
 */
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {}
