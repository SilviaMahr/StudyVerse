import { Component, Output, EventEmitter} from '@angular/core';
import { CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';

export interface PreselectionData {
  semester: string;
  ects: number;
  selectedDays: string [];
  preferredCourses: string;
}

export interface Weekdays {
  monday: boolean;
  tuesday: boolean;
  wednesday: boolean;
  thursday: boolean;
  friday: boolean;
  noRestriction: boolean;
}

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

  days: Weekdays = {
    monday: true,
    tuesday: true,
    wednesday: true,
    thursday: true,
    friday: true,
    noRestriction: true
  };

  constructor() {
    this.onDayChange();
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
    if (!this.selectedSemester) {
      console.warn('Bitte Semester wählen ')
      return;
    }
    if (this.selectedECTS > 40 || this.selectedECTS <= 0 ) {
      console.warn('Bitte gib eine gültige Zahl ein, aber maximal 40.')
      return;
    }

    const selectedDays: string [] = Object.keys(this.days)
      .filter(day => day !== 'noRestriction' && this.days[day as keyof Weekdays]);

    if (selectedDays.length === 0 && !this.days.noRestriction) {
      console.warn('Bitte wähle mindestens einen Tag aus.');
      return;
    }

    const data: PreselectionData = {
      semester: this.selectedSemester,
      ects: this.selectedECTS,
      selectedDays: selectedDays,
      preferredCourses: this.preferredCourses
    };

    this.startPlanning.emit(data);
  }
}
