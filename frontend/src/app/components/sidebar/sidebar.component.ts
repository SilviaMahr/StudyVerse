import {
  Component,
  ElementRef,
  OnInit,
  ViewChild,
  Renderer2,
  Inject,
  PLATFORM_ID,
  ChangeDetectorRef
} from '@angular/core';
import {CommonModule, isPlatformBrowser} from '@angular/common';
import { ThemeService} from '../../../services/theme.service';
import {RouterLink} from '@angular/router';
import {PlanningResponse} from '../../models/preselection.model';
import {PlanningService} from '../../../services/planning.service';

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

  recentPlannings: PlanningResponse[] = [];
  isLoading: boolean = true;
  error: string | null = null;


  constructor(
    protected themeService: ThemeService,
    private renderer: Renderer2,
    @Inject(PLATFORM_ID) private platformId: Object,
    private planningService: PlanningService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.applyInitialSidebarState();
    this.loadRecentPlannings();
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
    } else {
      this.toggleIconRef.nativeElement.src = assetPath + 'closeSidebarIcon.png';
      this.toggleIconRef.nativeElement.alt = 'Sidebar schließen';
    }
  }

  loadRecentPlannings(): void {
    this.isLoading = true;
    this.error = null;

    this.planningService.getRecentPlannings(5).subscribe({
      next: (response) => {
        this.recentPlannings = response.plannings;
        this.isLoading = false;
        console.log("Planungen geladen", this.recentPlannings);
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error("Fehler beim Laden der Planungen", err);
        this.error = "Planungen konnten nicht geladen werden.";
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
  }
}
