import {Component, ElementRef, Inject, OnInit, PLATFORM_ID, ViewChild, ChangeDetectorRef} from '@angular/core';
import {CommonModule} from '@angular/common';
import { Router } from '@angular/router';
import {Subscription} from 'rxjs';
import {ThemeService} from '../../../services/theme.service';
import {FormsModule, NgForm} from '@angular/forms';
import { APILoginService } from '../../../services/login/api.login.service';
import { HttpErrorResponse } from '@angular/common/http';
import {AuthService} from '../../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports : [
    CommonModule,
    FormsModule
  ],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
})

export class LoginComponent implements OnInit{
  @ViewChild('lightModeIcon', {static: true}) lightModeBtnRef!: ElementRef<HTMLImageElement>;
  @ViewChild('darkModeIcon', {static: true}) darkModeBtnRef!: ElementRef<HTMLImageElement>;

  private themeSubscription: Subscription | undefined;


  loginMessage: string | null = null;
  loginStatus: 'success' | 'error' | null = null;

  constructor(
    private router: Router,
    private themeService: ThemeService,
    private api: APILoginService,
    private authServie: AuthService,
    @Inject(PLATFORM_ID) private platformId: Object,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.themeSubscription = this.themeService.mode$.subscribe(mode => {
      this.updateModeIcons(mode === 'dark');
    })
  }

  onLogin(form: NgForm): void {
    this.loginMessage = null;
    this.loginStatus = null;

    this.api.login(form.value.email, form.value.pw).subscribe({
      next: (response: any) => {
        console.log('Login erfolgreich', response);
        if (response && response.access_token) {
          this.authServie.saveToken(response.access_token);
          this.router.navigate(['/landing']);
        } else {
          this.loginMessage = 'Login erfolgreich! Du wirst weitergeleitet ...';
          this.loginStatus = 'success';
        }

        this.cdr.detectChanges();

        setTimeout(() => {
          this.router.navigate(['/landing']);
        }, 1500);
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
  private updateModeIcons(isDarkMode: boolean): void {
    if (!this.lightModeBtnRef || !this.darkModeBtnRef) return;

    const assetPath = 'assets/';
    if (isDarkMode) {
      this.lightModeBtnRef.nativeElement.src = assetPath + "sunEmpty.png";
      this.darkModeBtnRef.nativeElement.src = assetPath + "moonFull.png";
    } else {
      this.lightModeBtnRef.nativeElement.src = assetPath + "sunFull.png";
      this.darkModeBtnRef.nativeElement.src = assetPath + "moonEmpty.png";
    }
  }

}
