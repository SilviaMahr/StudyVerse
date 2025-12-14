import {ChangeDetectorRef, Component, OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {CompletedLVAsUpdate, LVAModule} from '../../models/lva.models';
import {ProfileService} from '../../../services/profile.service';
import {Router} from '@angular/router';
import {forkJoin} from 'rxjs';

@Component ({
  selector: 'app-lva-management',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './lva-management.component.html',
  styleUrls: ['./lva-management.component.css']
})

export class LvaManagementComponent implements OnInit {
  pflichtfaecher: LVAModule[] = [];

  isLoading: boolean = true;
  isSaving: boolean = false;
  error: string | null = null;
  successMessage: string | null = null;
  constructor(
    private profileService: ProfileService,
    private cdr: ChangeDetectorRef,
    private router: Router
  ) { }

  ngOnInit() {
    this.isLoading = true;

    forkJoin({
      pflicht: this.profileService.getPflichtfaecher(),
    }).subscribe({
      next: (response) => {
        this.pflichtfaecher = response.pflicht.pflichtfaecher;
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error("Fehler beim Laden der LVA-Listen", err);
        this.error = "Die LVA-Listen konnten nicht geladen werden.";
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  onSave(): void {
    this.isSaving = true;
    this.successMessage = null;
    this.error = null;

    const completedIds: number [] = [];

    this.pflichtfaecher.forEach(module => {
      module.lvas.forEach(lva => {
        if (lva.is_completed) {
          completedIds.push(lva.id);
        }
      });
    });

    const updateData: CompletedLVAsUpdate = {
      lva_ids: completedIds
    };

    this.profileService.updateCompletedLvas(updateData).subscribe({
      next: (response) => {
        this.isSaving = false;
        this.successMessage = "Änderungen erfolgreich gespeichert!";
        this.cdr.detectChanges();

        setTimeout(() => {
          this.router.navigate(['/profile']);
        }, 2000);
      },
      error: (err) => {
        console.error("Fehler beim Speichern der LVAs:", err);
        this.error = "Speichern fehlgeschlagen.";
        this.isSaving = false;
        this.cdr.detectChanges();
      }
    });
  }
}
