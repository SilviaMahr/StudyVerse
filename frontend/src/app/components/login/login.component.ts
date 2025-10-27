import {Component, ElementRef, OnInit, ViewChild} from '@angular/core';
import {CommonModule} from '@angular/common';
import { Router } from '@angular/router';
import {Subscription} from 'rxjs';
import {ThemeService} from '../../../services/theme.service';
import {FormsModule} from '@angular/forms';

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

  constructor(
    private router: Router,
    private themeService: ThemeService
  ) { }

  ngOnInit() {
    this.themeSubscription = this.themeService.mode$.subscribe(mode => {
      this.updateModeIcons(mode === 'dark');
    })
  }

  ngOnDestroy(): void {
    if (this.themeSubscription) {
      this.themeSubscription.unsubscribe();
    }
  }

  onLogin(): void {
    this.router.navigate(['/landing']);
  }

  setDarkMode(): void {
    this.themeService.setDarkMode();
  }

  setLightMode(): void {
    this.themeService.setLightMode();
  }

  private updateModeIcons(isDarkMode: boolean): void {
    // Stellt sicher, dass die Refs existieren (wichtig bei globaler Komponente)
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
