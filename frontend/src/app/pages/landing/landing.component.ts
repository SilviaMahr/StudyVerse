import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import {SidebarComponent} from '../../components/sidebar/sidebar.component';
import {PreselectionComponent} from '../../components/preselection/preselection.component';
import {ProfileService} from '../../../services/profile.service';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [
    CommonModule,
    SidebarComponent,
    PreselectionComponent
  ],
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.css']
})
export class LandingComponent implements OnInit {
  username: string | undefined;
  isLoading: boolean = true;
  constructor(private profileService: ProfileService) {

  }

  ngOnInit() {
    this.loadUserProfile();
  }

  loadUserProfile() {
    this.profileService.getMyProfile().subscribe({
      next: (profile) => {
        this.username = profile.username;
        this.isLoading = false;
        console.log(this.username)
      },
      error: (err) => {
        console.error('Konnte Profil nicht laden', err);
        this.username = '';
        this.isLoading = false;
        console.log("Das hat nicht funktioniert")
      }
    });
  }
}
