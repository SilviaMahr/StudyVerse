import { Component} from '@angular/core';
import { CommonModule} from '@angular/common';
import {FormsModule, NgForm} from '@angular/forms';
import { PreselectionData, Weekdays} from '../../models/preselection.model';
import {PreselectionService} from '../../../services/preselection.service';
import {Router, RouterLink} from '@angular/router';


@Component( {
  selector: 'app-preselection',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink
  ],
  templateUrl: './preselection.component.html',
  styleUrls: ['./preselection.component.css']
})

export class PreselectionComponent {
  selectedSemester: string | null = null;
  selectedECTS: number | null = null;
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

  constructor(
    private preselectionService: PreselectionService,
    private router: Router
  )
  {
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

  onSubmit(form: NgForm): void {
    this.successMessage = null;
    this.errorMessage = null;

    if (form.invalid || !this.isDaySelected) {
      console.warn("Formular ist gültig oder kein Tag ausgewählt.");
      return;
    }

    this.successMessage = "Bitte habe einen Moment Geduld. Ich arbeite gerade an deiner Semesterplanung," +
      " das kann einen Augenblick dauern.";


    const data: PreselectionData = {
      semester: this.selectedSemester!,
      target_ects: this.selectedECTS!,
      preferred_days: this.getSelectedDaysArray(),
      mandatory_courses: this.preferredCourses
    };

    this.preselectionService.submitPreselection(data).subscribe({
      next: (response) => {
        console.log('Planung erfolgreich gesendet!', response);
        this.successMessage = "Planung wurde erfolgreich übermittelt";

        //TODO: implement when backend logic is implemented
       /* this.preselectionService.startRag(response.id).subscribe({
          next: (ragResponse: any) => {
            console.log('RAG-Analyse gestartet!', ragResponse);
            this.successMessage = "Planung erstellt und Analyse gestartet!";
            this.router.navigate(['/plan', response.id]);
          }
        })*/

        setTimeout(() => {
          this.successMessage = null;
          this.router.navigate(['/plan', response.id])
        }, 5000);
      },

      error: (error) => {
        console.error('Fehler beim Senden der Planung: ', error);

        this.successMessage = null;

        if (error.status === 401) {
          this.errorMessage = "Authentifizierung fehlgeschlagen. Bitte neu einloggen";
        } else if (error.status === 422) {
          this.errorMessage = "Die übermittelten Daten sind gültig. (Fehler 422)";
        } else {
          this.errorMessage = "Ein Fehler ist aufgetreten. Bitte versuche es später erneut."
        }
      }
    });
  }

  private getSelectedDaysArray(): string[] {
    const dayMap: { [key: string]: string} = {
      monday: "Montag",
      tuesday: "Dienstag",
      wednesday: "Mittwoch",
      thursday: "Donnerstag",
      friday: "Freitag"
    };

    return Object.entries(this.days)
      .filter(([key, value]) => value === true && key !== 'noRestriction')
      .map(([key, value]) => dayMap[key]);
  }
}
