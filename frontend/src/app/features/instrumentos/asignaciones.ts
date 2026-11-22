import {Component,inject} from '@angular/core';
import {DatePipe} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {RouterLink} from '@angular/router';
import {AsignacionesInstrumentoViewModel} from './asignaciones.viewmodel';
@Component({selector:'app-asignaciones-instrumento',imports:[DatePipe,FormsModule,RouterLink],providers:[AsignacionesInstrumentoViewModel],templateUrl:'./asignaciones.html',styleUrl:'../../shared/resultados/gestion.scss'})
export class AsignacionesInstrumentoComponent {readonly vm=inject(AsignacionesInstrumentoViewModel);}
