import {Injectable} from '@angular/core';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {AuthService} from './auth.service';
import {EMPTY, Observable} from 'rxjs';
import {PlanningResponse, RecentPlanningsResponse} from '../app/models/preselection.model';

@Injectable({
  providedIn: 'root'
})

export class PlanningService {
  private apiUrl='http://127.0.0.1:8000/plannings/recent';
  private baseUrl = 'http://127.0.0.1:8000/plannings';

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) {
  }

  public getRecentPlannings(limit: number = 5): Observable<RecentPlanningsResponse> {
    const token = this.authService.getToken();

    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    });

    const options = {
      headers: headers,
      params: {limit: limit.toString()}
    };

    return this.http.get<RecentPlanningsResponse>(this.apiUrl, options);
  }

  public getPlanningDetails(id: number): Observable<PlanningResponse> {
    const token = this.authService.getToken();

    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    });

    const url =`http://127.0.0.1:8000/plannings/${id}`;
    return this.http.get<PlanningResponse>(url, { headers: headers });
  }

  public deletePlanning(id: number): Observable<any> {
    const token = this.authService.getToken();
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    });

    const url = `${this.baseUrl}/${id}`;
    return this.http.delete<any>(url, { headers: headers });
  }
}
