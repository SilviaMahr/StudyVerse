import {Injectable} from '@angular/core';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {AuthService} from './auth.service';
import {Observable, EMPTY} from 'rxjs';
import {UserProfile, UserProfileUpdate} from '../app/models/user-profile.model';

@Injectable({
  providedIn: 'root'
})

export class ProfileService {
  private baseUrl = 'http://127.0.0.1:8000/profile';

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) { }

  private getAuthHeaders() : HttpHeaders | null {
    const token = this.authService.getToken();
    if (!token) {
      return null;
    }
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    });
  }

  public getMyProfile(): Observable<UserProfile> {
    const headers = this.getAuthHeaders();
    if (!headers) {
      return EMPTY;
    }
    return this.http.get<UserProfile>(`${this.baseUrl}/me`, { headers });
  }

  public updateMyProfile (data: UserProfileUpdate): Observable<UserProfile> {
    const headers = this.getAuthHeaders();
    if (!headers) {
      return EMPTY;
    }
    return this.http.put<UserProfile>(`${this.baseUrl}/me`, data, { headers });
  }
}
