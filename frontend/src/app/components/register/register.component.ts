import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  Validators,
  ReactiveFormsModule,
  AbstractControl,
  ValidationErrors
} from '@angular/forms';
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

  availableModules: LVAModule[] = [];
  selectedLvas: number[] = [];
  showPassword = false;
  showConfirmPassword = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private profileService: ProfileService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {
    this.registerForm = this.fb.group({
      username: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', Validators.required],
      studiengang: ['Bachelor Wirtschaftsinformatik']
    }, {validators: this.passwordMatchValidator});
  }

  passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
    const password = control.get('password');
    const confirmPassword = control.get('confirmPassword');

    if (!password || !confirmPassword) {
      return null;
    }

    return password.value === confirmPassword.value ? null: { passwordMismatch: true };
  }

  async onRegisterSubmit() {
    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.error = null;
    const { confirmPassword, ...registerData } = this.registerForm.value;

    try {
      await firstValueFrom(this.authService.register(registerData));

      await firstValueFrom(this.authService.login({
        username: registerData.email,
        password: registerData.password
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
