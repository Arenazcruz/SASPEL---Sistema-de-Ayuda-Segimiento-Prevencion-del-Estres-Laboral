import {Component,inject} from '@angular/core';
import {DatePipe} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {RouterLink} from '@angular/router';
import {AnimoViewModel} from './animo.viewmodel';
@Component({selector:'app-animo',imports:[DatePipe,FormsModule,RouterLink],providers:[AnimoViewModel],templateUrl:'./animo.html',styleUrl:'../../shared/resultados/consulta.scss',styles:['label{display:grid;gap:.4rem}fieldset{display:grid;gap:1rem;border:0}input,textarea{font:inherit;padding:.7rem;width:100%;box-sizing:border-box}article{margin:1rem 0}p{white-space:pre-wrap;overflow-wrap:anywhere}']})
export class AnimoComponent {readonly vm=inject(AnimoViewModel);}
