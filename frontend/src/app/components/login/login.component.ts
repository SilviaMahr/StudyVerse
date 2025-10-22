import { Component, OnInit, ElementRef, ViewChild, Renderer2, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common'; // Wichtig für SSR!

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
})
export class LoginComponent implements OnInit {
  @ViewChild('lightModeIcon', {static: true}) lightModeBtnRef!: ElementRef<HTMLImageElement>;
  @ViewChild('darkModeIcon', {static: true}) darkModeBtnRef!: ElementRef<HTMLImageElement>;
  @ViewChild('starContainer', { static: true}) starContainerRef!: ElementRef<HTMLDivElement>
  @ViewChild('planetContainer', { static: true}) planetContainerRef!: ElementRef<HTMLDivElement>


  constructor(
    private renderer: Renderer2,
    @Inject(PLATFORM_ID) private platformId: Object
  ) { }

  ngOnInit() {
    this.applyInitialMode();
    this.initBackgrounds();
  }

  private applyInitialMode(): void {
    if (isPlatformBrowser(this.platformId)) {
      const body = document.body; // <-- KONSISTENTER ZUGRIFF
      const saveMode = localStorage.getItem("mode");

      if (saveMode == "dark") {
        this.renderer.addClass(body, "dark-mode");
      } else {
        this.renderer.removeClass(body, "dark-mode");
      }
      this.updateModeIcons(saveMode === "dark");
    }
  }

  setDarkMode(): void {
    if (isPlatformBrowser(this.platformId)) {
      const body = document.body;
      this.renderer.addClass(body, "dark-mode");
      localStorage.setItem("mode", "dark");
      this.updateModeIcons(true);
    }
  }

  setLightMode(): void {
    if (isPlatformBrowser(this.platformId)) {
      const body = document.body;
      this.renderer.removeClass(body, "dark-mode");
      localStorage.setItem("mode", "day");
      this.updateModeIcons(false);
    }
  }

  private updateModeIcons(isDarkMode: boolean): void {
    const assetPath = 'assets/';

    if (isDarkMode) {
      this.lightModeBtnRef.nativeElement.src = assetPath + "sunEmpty.png";
      this.darkModeBtnRef.nativeElement.src = assetPath + "moonFull.png";
    } else {
      this.lightModeBtnRef.nativeElement.src = assetPath + "sunFull.png";
      this.darkModeBtnRef.nativeElement.src = assetPath + "moonEmpty.png";
    }
  }

  initBackgrounds(): void {
    if (isPlatformBrowser(this.platformId)) {
      const isDarkMode = localStorage.getItem('mode') === 'dark';

      this.generateStars(150);
      this.generateRandomPlanets(10);
    }
  }

  generateStars(count: number = 100): void {
    const starfield = this.starContainerRef.nativeElement;

    for (let i=0; i< count; i++) {
      const star = this.renderer.createElement('div');
      this.renderer.addClass(star, 'star');

      const size = Math.random() * 2 + 1;
      this.renderer.setStyle(star, 'width', `${size}px`);
      this.renderer.setStyle(star, 'height', `${size}px`);

      this.renderer.setStyle(star, 'top', `${Math.random() * 100}%`);
      this.renderer.setStyle(star, 'left', `${Math.random() * 100}%`);

      this.renderer.appendChild(starfield, star);
    }
  }

  generateRandomPlanets(count: number = 8): void {
    const container = this.planetContainerRef.nativeElement;
    const assetPath = 'assets/';

    const planetImages = [
      'greenPlanet.png',
      'flederPlanet.png',
      'redPlanet.png',
      'yellowPlanet.png'
    ];

    for (let i = 0; i < count; i++) {
      const planet = this.renderer.createElement('img');
      this.renderer.addClass(planet, 'planet');

      const src = planetImages[Math.floor(Math.random() * planetImages.length)];

      this.renderer.setAttribute(planet, 'src', assetPath + src);

      this.renderer.setStyle(planet, 'top', `${Math.random() * 90}%`);
      this.renderer.setStyle(planet, 'left', `${Math.random() * 90}%`);

      const size = Math.random() * 40 + 40; // 40–80px
      this.renderer.setStyle(planet, 'width', `${size}px`);
      this.renderer.setStyle(planet, 'height', `${size}px`);

      this.renderer.appendChild(container, planet);
    }
  }
}
