import { Routes } from '@angular/router';
import { LoginComponent} from './pages/login/login.component';
import { LandingComponent} from './pages/landing/landing.component';
import {PreselectionComponent} from './components/preselection/preselection.component';
import {ProfileEditComponent} from './components/profile-edit/profile-edit.component';
import { MainLayoutComponent} from './components/main-layout/main-layout.component';
import {authGuard} from '../services/auth.guard';

export const routes: Routes = [
  {
    path: 'landing',
    component: LandingComponent,
    canActivate: [authGuard]
  },

  {
    path: 'login',
    component: LoginComponent
  },

  {
    path: '',
    redirectTo: '/login',
    pathMatch: 'full'
  },

  {
    path: '',
    component: MainLayoutComponent,
    canActivate: [authGuard],
    children: [
      {
        path: 'plan',
        component: PreselectionComponent
      },
      {
        path: 'profile',
        component: ProfileEditComponent
      }
    ]
  }
];
