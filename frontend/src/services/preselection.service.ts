import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import {EMPTY, Observable} from 'rxjs';
import {PreselectionData, RAGStartResponse} from '../app/models/preselection.model';
import { AuthService } from './auth.service';


@Injectable({
  providedIn: 'root'
})

export class PreselectionService {

  private baseUrl = 'http://127.0.0.1:8000';

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) { }

  /**
   * send preselection to backend
   */
  submitPreselection(data: PreselectionData): Observable<any> {

    const token = this.authService.getToken();

    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    });

    const url = `${this.baseUrl}/plannings/new`;


    return this.http.post<any>(url, data, { headers: headers });
  }

  public startRag(planningId: number): Observable<RAGStartResponse> {
    const token = this.authService.getToken();
    if (!token) return EMPTY;

    const url = `${this.baseUrl}/plannings/${planningId}/start-rag`;

    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    });

    return this.http.post<RAGStartResponse>(url, {}, { headers: headers});
  }
}
