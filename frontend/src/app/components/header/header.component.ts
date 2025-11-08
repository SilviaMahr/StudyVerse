import { ChangeDetectionStrategy, Component, ViewEncapsulation} from '@angular/core';
import {LogoutComponent} from '../logout/logout.component';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [
    LogoutComponent
  ],
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css'],
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class HeaderComponent {
  constructor() { }
}
