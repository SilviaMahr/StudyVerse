import { Routes } from '@angular/router';
import { LoginComponent} from './components/login/login.component';
import { LandingComponent} from './components/landing/landing.component';

export const routes: Routes = [
  {
    path: 'landing',
    component: LandingComponent
  },

  {
    path: 'login',
    component: LoginComponent
  },

  {
    path: '',
    redirectTo: '/login',
    pathMatch: 'full'
  }
];
