import {Component,inject} from '@angular/core';
import {DatePipe} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {RouterLink} from '@angular/router';
import {NotificacionesViewModel} from './notificaciones.viewmodel';
@Component({selector:'app-notificaciones',imports:[DatePipe,FormsModule,RouterLink],providers:[NotificacionesViewModel],styleUrl:'../../shared/resultados/consulta.scss',templateUrl:'./notificaciones.html'})
export class NotificacionesComponent {readonly vm=inject(NotificacionesViewModel);}
