import {Component,inject} from '@angular/core';
import {DatePipe} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {RouterLink} from '@angular/router';
import {EvolucionViewModel} from './evolucion.viewmodel';
@Component({selector:'app-evolucion',imports:[DatePipe,FormsModule,RouterLink],providers:[EvolucionViewModel],templateUrl:'./evolucion.html',styleUrl:'../../shared/resultados/gestion.scss',styles:['svg{width:100%;max-height:220px;background:#f4f7f1}table{width:100%;text-align:left}td,th{padding:.6rem}form{display:flex;gap:1rem;flex-wrap:wrap}']})
export class EvolucionComponent {readonly vm=inject(EvolucionViewModel);}
