import {Component, ChangeDetectorRef} from '@angular/core';
import {CommonModule} from '@angular/common';
import {Router, RouterLink} from '@angular/router';
import {ThemeService} from '../../../services/theme.service';
import {FormsModule, NgForm} from '@angular/forms';
import { APILoginService } from '../../../services/login/api.login.service';
import { HttpErrorResponse } from '@angular/common/http';
import {AuthService} from '../../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink
  ],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
})

export class LoginComponent {
  loginMessage: string | null = null;
  loginStatus: 'success' | 'error' | null = null;

  constructor(
    private router: Router,
    protected themeService: ThemeService,
    private api: APILoginService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef
  ) { }

  onLogin(form: NgForm): void {
    this.loginMessage = null;
    this.loginStatus = null;

    this.api.login(form.value.email, form.value.pw).subscribe({
      next: (response: any) => {
        console.log('Login erfolgreich', response);

        if (response && response.access_token) {
          this.authService.saveToken(response.access_token);
          this.loginMessage = 'Login erfolgreich! Du wirst weitergeleitet ...';
          this.loginStatus = 'success';
          this.cdr.detectChanges();

          setTimeout(() => {
            this.router.navigate(['/landing']);
          }, 1500);
        } else {
          this.loginStatus = 'error';
          this.loginMessage = 'Login fehlgeschlagen. Probiere es später erneut.'
          this.cdr.detectChanges();
          }
        },

      error: (err: HttpErrorResponse) => {
        this.loginStatus = 'error';
        if (err.status === 401) {
          this.loginMessage = 'E-Mail-Adresse oder Passwort ist falsch.';
        } else {
          this.loginMessage = 'Ein Fehler ist aufgetreten. Bitte versuche es später erneut.';
        }

        this.cdr.detectChanges();
      }
    });
  }

  setDarkMode(): void {
    this.themeService.setDarkMode();
  }

  setLightMode(): void {
    this.themeService.setLightMode();
  }
}
