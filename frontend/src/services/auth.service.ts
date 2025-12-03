import { Inject, Injectable, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import {BehaviorSubject, Observable, tap} from 'rxjs';
import { HttpClient} from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  private readonly TOKEN_KEY = 'auth_token';
  private readonly API_URL = 'http://127.0.0.1:8000/auth';

  private isBrowser: boolean;
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(false);

  public isAuthenticated$ =this.isAuthenticatedSubject.asObservable();

  constructor(
    @Inject(PLATFORM_ID) private platformId: Object,
    private http: HttpClient
    ) {
    this.isBrowser = isPlatformBrowser(this.platformId);

    if (this.isBrowser) {
      const token = localStorage.getItem(this.TOKEN_KEY);
      this.isAuthenticatedSubject.next(!!token);
    }
  }

  register(userData: any): Observable<any> {
    return this.http.post(`${this.API_URL}/register`, userData);
  }

  login(credentials: { username: string, password: string }): Observable<any> {
    const formData = new FormData();
    formData.append('username', credentials.username); // FastAPI nutzt 'username' auch für Email
    formData.append('password', credentials.password);

    return this.http.post(`${this.API_URL}/login`, formData).pipe(
      // 'tap' führt Seiteneffekte aus, ohne den Datenfluss zu ändern
      tap((response: any) => {
        if (response.access_token) {
          this.saveToken(response.access_token);
        }
      })
    );
  }

  saveToken(token: string): void {
    if (isPlatformBrowser(this.platformId)) {
      localStorage.setItem(this.TOKEN_KEY, token);
      this.isAuthenticatedSubject.next(true);
    }
  }

  getToken(): string | null {
    if (isPlatformBrowser(this.platformId)) {
      return localStorage.getItem(this.TOKEN_KEY);
    }
    return null;
  }

  isAuthenticated(): boolean {
    return this.isAuthenticatedSubject.value;
  }

  logout(): void {
    if (isPlatformBrowser(this.platformId)) {
      localStorage.removeItem(this.TOKEN_KEY);
      this.isAuthenticatedSubject.next(false);
    }
  }
}
