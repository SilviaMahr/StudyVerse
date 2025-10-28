import {Component, ElementRef, OnDestroy, OnInit, ViewChild, Renderer2} from '@angular/core';
import { CommonModule} from '@angular/common';
import { ThemeService} from '../../../services/theme.service';
import { Subscription} from 'rxjs';

@Component( {
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})

export class SidebarComponent implements OnInit, OnDestroy {
  @ViewChild('lightModeIcon', {static: true}) lightModeBtnRef!: ElementRef<HTMLImageElement>;
  @ViewChild('darkModeIcon', {static: true}) darkModeBtnRef!: ElementRef<HTMLImageElement>;
  @ViewChild('sidebar') sidebarRef!: ElementRef<HTMLElement>;
  @ViewChild('toggleIcon') toggleIconRef!: ElementRef<HTMLImageElement>;

  isDarkMode = false;
  private themeSubscription: Subscription | undefined;
  isCollapsed = false;

  constructor(
    private themeService: ThemeService,
    private renderer: Renderer2
  ) { }

  ngOnInit() {
    this.themeSubscription = this.themeService.mode$.subscribe(mode => {
      this.isDarkMode = (mode === 'dark');

      setTimeout(() => {
        this.updateModeIcons(this.isDarkMode);
      }, 0);
    })
  }

  ngOnDestroy() {
    if (this.themeSubscription) {
      this.themeSubscription.unsubscribe();
    }
  }

  toggleDarkMode (): void {
    this.themeService.setLightMode();
  }

  toggleLightMode (): void {
    this.themeService.setDarkMode();
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

  toggleSidebar(): void {
    this.isCollapsed = !this.isCollapsed;
    const assetPath = 'assets/';

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
}
