import {Component, ElementRef, OnInit, ViewChild, Renderer2, Inject, PLATFORM_ID} from '@angular/core';
import {CommonModule, isPlatformBrowser} from '@angular/common';
import { ThemeService} from '../../../services/theme.service';
import {RouterLink} from '@angular/router';

@Component( {
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})

export class SidebarComponent implements OnInit {
  @ViewChild('sidebar') sidebarRef!: ElementRef<HTMLElement>;
  @ViewChild('toggleIcon') toggleIconRef!: ElementRef<HTMLImageElement>;

  isCollapsed = false;

  constructor(
    protected themeService: ThemeService,
    private renderer: Renderer2,
    @Inject(PLATFORM_ID) private platformId: Object
  ) { }

  ngOnInit() {
    this.applyInitialSidebarState()
  }

  private applyInitialSidebarState(): void {
      if (isPlatformBrowser(this.platformId)) {
      const savedState = localStorage.getItem('sidebarCollapsed');
      this.isCollapsed = savedState === 'true';

      setTimeout(() => {
        if (this.isCollapsed) {
          this.renderer.addClass(this.sidebarRef.nativeElement, 'collapsed');
        } else {
          this.renderer.removeClass(this.sidebarRef.nativeElement, 'collapsed');
        }
        this.updateToggleIcon();
      }, 0);
    }
  }

  toggleDarkMode (): void {
    this.themeService.setLightMode();
  }

  toggleLightMode (): void {
    this.themeService.setDarkMode();
  }

  toggleSidebar(): void {
    this.isCollapsed = !this.isCollapsed;
    const assetPath = 'assets/';

    if (isPlatformBrowser(this.platformId)) {
      localStorage.setItem('sidebarCollapsed', this.isCollapsed.toString());
    }

    if (this.isCollapsed) {
      // close sidebar
      this.renderer.addClass(this.sidebarRef.nativeElement, 'collapsed');
      this.toggleIconRef.nativeElement.src = assetPath + 'openSidebarIcon.png';
      this.toggleIconRef.nativeElement.alt = 'Sidebar öffnen';
    } else {
      //open sidebar
      this.renderer.removeClass(this.sidebarRef.nativeElement, 'collapsed');
      this.toggleIconRef.nativeElement.src = assetPath + 'closeSidebarIcon.png';
      this.toggleIconRef.nativeElement.alt = 'Sidebar schließen';
    }
  }

  private updateToggleIcon(): void {
      if (!this.toggleIconRef) return;

    const assetPath = 'assets/';
    if (this.isCollapsed) {
      this.toggleIconRef.nativeElement.src = assetPath + 'openSidebarIcon.png';
      this.toggleIconRef.nativeElement.alt = 'Sidebar öffnen';
    } else {
      this.toggleIconRef.nativeElement.src = assetPath + 'closeSidebarIcon.png';
      this.toggleIconRef.nativeElement.alt = 'Sidebar schließen';
    }
  }
}
