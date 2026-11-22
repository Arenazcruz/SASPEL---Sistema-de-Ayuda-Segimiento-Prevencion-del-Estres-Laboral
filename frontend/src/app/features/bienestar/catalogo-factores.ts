import {Component,inject} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {RouterLink} from '@angular/router';
import {CatalogoFactoresViewModel} from './catalogo-factores.viewmodel';
@Component({selector:'app-catalogo-factores',imports:[FormsModule,RouterLink],providers:[CatalogoFactoresViewModel],templateUrl:'./catalogo-factores.html',styleUrl:'../../shared/resultados/consulta.scss',styles:['label{display:grid;gap:.4rem}fieldset{display:grid;gap:1rem;border:0}input,textarea{font:inherit;padding:.7rem}article{margin:1rem 0}']})
export class CatalogoFactoresComponent {readonly vm=inject(CatalogoFactoresViewModel);}
