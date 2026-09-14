/**
 * Pantalla del formulario de acceso. LoginViewModel valida, llama AuthService y navega al
 * panel recibido; modificar mensajes o envío en el ViewModel y presentación en
 * login.html/login.scss.
 */
import { Component, inject } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Brand } from '../../../shared/brand/brand';
import { LoginViewModel } from './login.viewmodel';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, RouterLink, Brand],
  providers: [LoginViewModel],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class LoginComponent {
  readonly vm = inject(LoginViewModel);
}
