import {Component,inject} from '@angular/core';
import {DatePipe} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {RouterLink} from '@angular/router';
import {GobiernoViewModel} from './gobierno.viewmodel';
import {AuthService} from '../../core/auth/auth.service';
@Component({selector:'app-gobierno',imports:[DatePipe,FormsModule,RouterLink],providers:[GobiernoViewModel],templateUrl:'./gobierno.html',styleUrl:'../../shared/resultados/gestion.scss',styles:['fieldset{display:grid;gap:1rem;border:0}label{display:grid;gap:.4rem}textarea{min-height:160px}pre{white-space:pre-wrap;overflow-wrap:anywhere}article{margin:1rem 0}']})
export class GobiernoComponent {readonly vm=inject(GobiernoViewModel);readonly auth=inject(AuthService);}
