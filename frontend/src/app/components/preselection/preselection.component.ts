import { Component, Output, EventEmitter} from '@angular/core';
import { CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import { PreselectionData, Weekdays} from '../../models/preselection.model';
import {PreselectionService} from '../../../services/preselection.service';


@Component( {
  selector: 'app-preselection',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './preselection.component.html',
  styleUrls: ['./preselection.component.css']
})

export class PreselectionComponent {
  @Output() startPlanning = new EventEmitter<PreselectionData>();

  selectedSemester: string = 'WS2025/26';
  selectedECTS: number = 30;
  preferredCourses: string = '';
  successMessage: string | null = null;
  errorMessage: string | null = null;

  days: Weekdays = {
    monday: true,
    tuesday: true,
    wednesday: true,
    thursday: true,
    friday: true,
    noRestriction: true
  };

  constructor(private preselectionService: PreselectionService) {
    this.onDayChange();
  }

  public get isDaySelected(): boolean {
    return this.days.monday ||
      this.days.tuesday ||
      this.days.wednesday ||
      this.days.thursday ||
      this.days.friday ||
      this.days.noRestriction;
  }

  onDayChange(): void {
    this.days.noRestriction = this.days.monday && this.days.tuesday && this.days.wednesday && this.days.thursday && this.days.friday;
  }

  onNoRestrictionChange(): void {
    const status = this.days.noRestriction;
    this.days.monday = status;
    this.days.tuesday = status;
    this.days.wednesday = status;
    this.days.thursday = status;
    this.days.friday = status;
  }

  onSubmit(): void {
    this.successMessage = null;
    this.errorMessage = null;


    if (!this.selectedSemester) {
      return;
    }
    if (this.selectedECTS > 60 || this.selectedECTS <= 0) {
      return;
    }
    if (!this.isDaySelected) {
      return;
    }

    this.successMessage = "Bitte habe einen Moment Geduld. Ich arbeite gerade an deiner Semesterplanung, das kann einen Moment dauern."
    setTimeout(() => {
      this.successMessage = "";
    }, 5000);

    const data: PreselectionData = {
      semester: this.selectedSemester,
      ects: this.selectedECTS,
      selectedDays: this.getSelectedDaysArray(),
      preferredCourses: this.preferredCourses
    };

    this.preselectionService.submitPreselection(data).subscribe({
      next: (response) => {
        console.log('Planung erfolgreich gesendet!', response);
        this.successMessage = "Planung wurde erfolgfreich übermittelt";

        setTimeout(() => {
          this.successMessage = null;
        }, 5000);
      },

      error: (error) => {
        console.error('Fehler beim Senden der Planung: ', error);

        this.successMessage = null;

        if (error.status === 401) {
          this.errorMessage = "Authentifizierung fehlgeschlagen. Bitte neu einloggen";
        } else {
          this.errorMessage = "Ein Fehler ist aufgetreten. Bitte versuche es später erneut";
        }
      }
    });

    this.startPlanning.emit(data);
  }

  private getSelectedDaysArray(): string[] {
    return Object.entries(this.days)
      .filter(([key, value]) => value === true && key !== 'noRestriction')
      .map(([key, value]) => key);
  }
}
