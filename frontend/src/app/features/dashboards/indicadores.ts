import {Component,inject} from '@angular/core';
import {DatePipe} from '@angular/common';
import {IndicadoresViewModel} from './indicadores.viewmodel';
@Component({selector:'app-indicadores',imports:[DatePipe],providers:[IndicadoresViewModel],templateUrl:'./indicadores.html',styles:['.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin:20px 0}.cards article{background:#fff;border:1px solid #d4dfd2;border-radius:8px;padding:20px}.cards strong{display:block;font-size:28px;color:#21472d}']})
export class IndicadoresComponent {readonly vm=inject(IndicadoresViewModel);}
