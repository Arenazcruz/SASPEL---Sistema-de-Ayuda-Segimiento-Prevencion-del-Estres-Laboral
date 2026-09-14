/**
 * Arranca Angular con App y appConfig. Revisar app.config.ts para proveedores/rutas; este
 * punto solo inicia la aplicación y registra fallos de arranque.
 */
import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';

bootstrapApplication(App, appConfig)
  .catch((err) => console.error(err));
