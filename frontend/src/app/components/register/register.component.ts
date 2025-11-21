import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { AuthService} from '../../../services/auth.service';
import { ProfileService } from '../../../services/profile.service';
import { LVAModule, CompletedLVAsUpdate } from '../../models/lva.models';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css']
})
export class RegisterComponent {
  step: 'account' | 'lvas' = 'account';

  registerForm: FormGroup;
  isLoading = false;
  error: string | null = null;

  availableModules: LVAModule[] = []; // Typisiert mit deinem Model
  selectedLvas: number[] = [];        // Liste der ausgewählten IDs

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private profileService: ProfileService, // Hier nutzen wir jetzt deinen ProfileService
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {
    this.registerForm = this.fb.group({
      username: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      studiengang: ['Bachelor Wirtschaftsinformatik']
    });
  }

  async onRegisterSubmit() {
    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.error = null;
    const formValue = this.registerForm.value;

    try {
      await firstValueFrom(this.authService.register(formValue));

      await firstValueFrom(this.authService.login({
        username: formValue.email, // Backend erwartet username als Feld
        password: formValue.password
      }));

      await this.loadAvailableLvas();

      this.step = 'lvas';

    } catch (err: any) {
      console.error('Fehler bei Registrierung/Login:', err);
      if (err.status === 400 && err.error?.detail) {
        this.error = err.error.detail;
      } else {
        this.error = 'Registrierung fehlgeschlagen. Bitte überprüfe deine Eingaben.';
      }
    } finally {
      this.isLoading = false;
      this.cdr.detectChanges();
    }
  }


  async loadAvailableLvas(): Promise<void> {
    try {
      const response = await firstValueFrom(this.profileService.getPflichtfaecher());
      this.availableModules = response.pflichtfaecher || [];

    } catch (err) {
      console.error("Konnte Fächer nicht laden", err);
      this.availableModules = [];
    }
  }

  /**
   * Klick-Handler für die LVA-Auswahl
   */
  toggleLva(lvaId: number): void {
    if (this.selectedLvas.includes(lvaId)) {
      this.selectedLvas = this.selectedLvas.filter(id => id !== lvaId);
    } else {
      this.selectedLvas.push(lvaId);
    }
  }

  async finishRegistration() {
    this.isLoading = true;

    try {
      const updateData: CompletedLVAsUpdate = {
        lva_ids: this.selectedLvas
      };

      await firstValueFrom(this.profileService.updateCompletedLvas(updateData));

      this.router.navigate(['/help']);

    } catch (err) {
      console.error("Fehler beim Speichern der LVAs:", err);
      this.router.navigate(['/help']);
    } finally {
      this.isLoading = false;
    }
  }
}
