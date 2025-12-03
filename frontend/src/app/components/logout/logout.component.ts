import {Component} from '@angular/core';
import {CommonModule} from '@angular/common';
import {AuthService} from '../../../services/auth.service';
import {Router} from '@angular/router';
import {ThemeService} from '../../../services/theme.service';

@Component({
  selector: 'app-logout',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './logout.component.html',
  styleUrls: ['./logout.component.css']
})

export class LogoutComponent {
  public showConfirmationModal = false;

  constructor(
    private authService: AuthService,
    private router: Router,
    public themeService: ThemeService
  ) { }

  openModal(): void {
    event?.preventDefault();
    this.showConfirmationModal = true;
  }

  closeModal(): void {
    this.showConfirmationModal = false;
  }

  confirmLogout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
    this.closeModal();
  }
}
