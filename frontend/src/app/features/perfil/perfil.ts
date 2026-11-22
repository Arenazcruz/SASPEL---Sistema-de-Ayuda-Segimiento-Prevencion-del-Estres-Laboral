import {Component,inject} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {RouterLink} from '@angular/router';
import {PerfilViewModel} from './perfil.viewmodel';
import {AuthService} from '../../core/auth/auth.service';
@Component({selector:'app-perfil',imports:[FormsModule,RouterLink],providers:[PerfilViewModel],templateUrl:'./perfil.html',styleUrl:'../../shared/resultados/gestion.scss',styles:['fieldset{display:grid;gap:1rem;border:0}label{display:grid;gap:.4rem}']})
export class PerfilComponent {readonly vm=inject(PerfilViewModel);readonly auth=inject(AuthService);}
