import {Component,inject} from '@angular/core';
import {DatePipe} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {RouterLink} from '@angular/router';
import {SeguimientoViewModel} from './seguimiento.viewmodel';
@Component({selector:'app-seguimiento',imports:[DatePipe,FormsModule,RouterLink],providers:[SeguimientoViewModel],templateUrl:'./seguimiento.html',styleUrl:'../../../shared/resultados/consulta.scss',styles:[
 'form{display:grid;gap:1rem}label{display:grid;gap:.4rem}input,textarea{font:inherit;padding:.7rem;width:100%;box-sizing:border-box}fieldset{border:0;display:grid;gap:1rem}article{margin:1rem 0}p{white-space:pre-wrap;overflow-wrap:anywhere}'
]})
export class SeguimientoComponent {readonly vm=inject(SeguimientoViewModel);}
