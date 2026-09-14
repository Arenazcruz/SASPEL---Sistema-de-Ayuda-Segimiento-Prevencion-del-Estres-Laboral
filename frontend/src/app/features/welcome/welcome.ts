/**
 * Página pública de bienvenida: compone marca, ilustración y enlace al login. No consulta
 * datos; contenido y diseño están en welcome.html/welcome.scss.
 */
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { WelcomeArt } from './welcome-art';
import { Brand } from '../../shared/brand/brand';

@Component({
  selector: 'app-welcome',
  imports: [RouterLink, Brand, WelcomeArt],
  templateUrl: './welcome.html',
  styleUrl: './welcome.scss',
})
export class Welcome {}
