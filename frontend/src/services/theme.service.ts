import { Inject, Injectable, PLATFORM_ID, Renderer2, RendererFactory2 } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private renderer: Renderer2;
  private _mode = new BehaviorSubject<'day' | 'dark'>('day');

  /**
   * Ein Observable, das Komponenten abonnieren können,
   * um über Mode-Änderungen informiert zu werden.
   */
  public mode$ = this._mode.asObservable();

  constructor(
    private rendererFactory: RendererFactory2,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    // Renderer2 kann nicht direkt in einen Service injiziert werden,
    // also verwenden wir die Factory.
    this.renderer = this.rendererFactory.createRenderer(null, null);
    this.applyInitialMode();
  }

  private applyInitialMode(): void {
    if (isPlatformBrowser(this.platformId)) {
      const body = document.body;
      const saveMode = localStorage.getItem("mode") as 'day' | 'dark' | null;

      if (saveMode === "dark") {
        this.renderer.addClass(body, "dark-mode");
        this._mode.next('dark');
      } else {
        this.renderer.removeClass(body, "dark-mode");
        this._mode.next('day'); // Standard ist 'day'
      }
    }
  }

  setDarkMode(): void {
    if (isPlatformBrowser(this.platformId)) {
      const body = document.body;
      this.renderer.addClass(body, "dark-mode");
      localStorage.setItem("mode", "dark");
      this._mode.next('dark');
    }
  }

  setLightMode(): void {
    if (isPlatformBrowser(this.platformId)) {
      const body = document.body;
      this.renderer.removeClass(body, "dark-mode");
      localStorage.setItem("mode", "day");
      this._mode.next('day');
    }
  }
}
