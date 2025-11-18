import { ChangeDetectionStrategy, Component, ViewEncapsulation} from '@angular/core';
import {LogoutComponent} from '../logout/logout.component';
import {Observable} from 'rxjs';
import {AuthService} from '../../../services/auth.service';
import {AsyncPipe} from '@angular/common';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [
    LogoutComponent,
    AsyncPipe
  ],
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css'],
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class HeaderComponent {
  public isLoggedIn$: Observable<boolean>;

  constructor(
    private authService: AuthService
  ) {
    this.isLoggedIn$ = this.authService.isAuthenticated$;
  }
}
