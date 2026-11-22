import {Component,inject} from '@angular/core';
import {DatePipe} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {RouterLink} from '@angular/router';
import {RecomendacionesViewModel} from './recomendaciones.viewmodel';
@Component({selector:'app-recomendaciones',imports:[DatePipe,FormsModule,RouterLink],providers:[RecomendacionesViewModel],templateUrl:'./recomendaciones.html',styleUrl:'../../shared/resultados/gestion.scss'})
export class RecomendacionesComponent {readonly vm=inject(RecomendacionesViewModel);}
