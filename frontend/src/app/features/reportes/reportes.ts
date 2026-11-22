import {Component,inject} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {RouterLink} from '@angular/router';
import {ReportesViewModel} from './reportes.viewmodel';
@Component({selector:'app-reportes',imports:[FormsModule,RouterLink],providers:[ReportesViewModel],templateUrl:'./reportes.html',styleUrl:'../../shared/resultados/consulta.scss',styles:['form{display:flex;flex-wrap:wrap;gap:16px;align-items:end;margin:24px 0}label{display:grid;gap:6px}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:12px;border-bottom:1px solid #d4dfd2}']})
export class ReportesComponent {readonly vm=inject(ReportesViewModel);}
