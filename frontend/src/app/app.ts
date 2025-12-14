import {Component, Inject, OnInit, PLATFORM_ID, Renderer2, ViewChild, ElementRef} from '@angular/core';
import { RouterOutlet } from '@angular/router';
import {HeaderComponent} from './components/header/header.component';
import {CommonModule, isPlatformBrowser} from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    HeaderComponent
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})

export class App implements OnInit {
  title = 'STUDYverse';

  @ViewChild('starContainer', { static: true}) starContainerRef!: ElementRef<HTMLDivElement>
  @ViewChild('planetContainer', { static: true}) planetContainerRef!: ElementRef<HTMLDivElement>

  constructor(
    private renderer: Renderer2,
    @Inject(PLATFORM_ID) private platformId: Object
  ) { }

  ngOnInit() {
    this.initBackgrounds();
  }

  initBackgrounds(): void {
    if (isPlatformBrowser(this.platformId)) {
      // Stellt sicher, dass die Refs existieren
      if (!this.starContainerRef || !this.planetContainerRef) return;

      this.generateStars(150);
      this.generateRandomPlanets(10);
    }
  }

  generateStars(count: number = 100): void {
    const starfield = this.starContainerRef.nativeElement;
    starfield.innerHTML = '';

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
    container.innerHTML = '';
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

