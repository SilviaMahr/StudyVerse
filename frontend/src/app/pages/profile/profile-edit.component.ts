import {ChangeDetectorRef, Component} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {UserProfile, UserProfileUpdate} from '../../models/user-profile.model';
import {ProfileService} from '../../../services/profile.service';
import {RouterLink} from '@angular/router';

@Component ({
  selector: 'app-profile-edit',
  standalone : true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink
  ],
  templateUrl: './profile-edit.component.html',
  styleUrls: ['./profile-edit.component.css']
})

export class ProfileEditComponent {
  userName: string = '';
  email: string = '';
  selectedDegree: string = '';

  isLoading: boolean = true;
  errorMessage: string | null = null;
  successMessage: string | null = null;

  protected originalData: UserProfile | null = null;

  constructor(
    private profileService: ProfileService,
    private cdr: ChangeDetectorRef
  ) {
  }

  ngOnInit(): void {
    this.isLoading = true;
    this.profileService.getMyProfile().subscribe({
      next: (data) => {
        this.userName = data.username;
        this.email = data.email;
        this.selectedDegree = data.studiengang;

        this.originalData = data;

        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error("Fehler beim Laden des Profils:", err);
        this.errorMessage = "Profil konnte nicht geladen werden.";
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  onSubmit(): void {
   this.isLoading = true;
   this.successMessage = null;
   this.errorMessage = null;

   const updateData: UserProfileUpdate = {};

   if (this.userName !== this.originalData?.username){
     updateData.username = this.userName;
   }
   if (this.email !== this.originalData?.email) {
     updateData.email = this.email;
   }
   if (this.selectedDegree !== this.originalData?.studiengang){
     updateData.studiengang = this.selectedDegree;
   }

   if (Object.keys(updateData).length === 0 ){
     this.successMessage = "Es gab keine Änderungen zum Speichern.";
     this.isLoading = false;
     setTimeout(() =>
     this.successMessage = null, 3000);
     return;
   }

   this.profileService.updateMyProfile(updateData).subscribe({
     next: (updateData) => {
       this.userName = updateData.username;
       this.email = updateData.email;
       this.selectedDegree = updateData.studiengang;
       this.originalData = updateData;

       this.isLoading = false;
       this.successMessage = "Profil erfolgreich gespeichert!";
       this.cdr.detectChanges();

       setTimeout(() =>
       this.successMessage = null, 3000);
     },
     error: (err) => {
       this.errorMessage = err.error?.detail || "Ein Fehler ist aufgetreten.";
       this.isLoading = false;
       this.cdr.detectChanges();
     }
   });
  }
}
