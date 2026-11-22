import {Component,inject} from '@angular/core';
import {DatePipe} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {RouterLink} from '@angular/router';
import {CitasViewModel} from './citas.viewmodel';
@Component({selector:'app-citas',imports:[FormsModule,RouterLink,DatePipe],providers:[CitasViewModel],templateUrl:'./citas.html',styleUrl:'../../shared/resultados/consulta.scss',styles:['form, fieldset {display:grid;gap:12px;} label {display:grid;gap:5px;} input,select,textarea {padding:10px;max-width:100%;} article {margin-block:20px;padding:20px;border:1px solid #cad8c7;} .acciones {display:flex;gap:10px;flex-wrap:wrap;}']})
export class Citas {readonly vm=inject(CitasViewModel);}
