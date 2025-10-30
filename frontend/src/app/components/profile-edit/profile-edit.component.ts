import {Component} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';

@Component ({
  selector: 'app-profile-edit',
  standalone : true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './profile-edit.component.html',
  styleUrls: ['./profile-edit.component.css']
})

export class ProfileEditComponent {
  userName: string = 'Max Mustermann'; //TODO: load data
  selectedDegree: string = 'Bachelor Wirtschaftsinformatik';
  completedCoursesCount: string = ''; //TODO: replace when backend logic is implemented
  electiveWishlistCount: string = ''; //TODO: replace when backend logic is implemented

  constructor() {
    //TODO: load data
  }

  onSubmit(): void {
    console.log('Speichere Profil:', this.userName, this.selectedDegree);
    //TODO: implement logic to save data
  }

  openCompletedCoursesModal() : void {
    console.log('Öffne Modal für absolviere LVAs...');
    //TODO: implement logic
  }

  openWishlistModal(): void {
    console.log('Öffne Modal für Wunschwahlfächer...');
    //TODO: implement logic
  }
}
