import { Routes } from '@angular/router';
import { LoginComponent} from './pages/login/login.component';
import { LandingComponent} from './pages/landing/landing.component';
import {PreselectionComponent} from './components/preselection/preselection.component';
import {ProfileEditComponent} from './pages/profile/profile-edit.component';
import { MainLayoutComponent} from './components/main-layout/main-layout.component';
import {authGuard} from '../services/auth.guard';
import {LvaManagementComponent} from './components/lva-management/lva-management.component';
import {HelpComponent} from './components/help/help.component';
import {PlanWorkspaceComponent} from './components/plan-workspace/plan-workspace.component';

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
      },
      {
        path: 'plan/:id',
        component: PlanWorkspaceComponent
      },
      {
        path: 'lva-management',
        component: LvaManagementComponent
      },

      {
        path: 'help',
        component: HelpComponent
      }
    ]
  }
];
