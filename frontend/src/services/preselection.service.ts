import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PreselectionData} from '../app/models/preselection.model';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class PreselectionService {

  private apiUrl = 'http://127.0.0.1:8000/api/start-planning';

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


    return this.http.post<any>(this.apiUrl, data, { headers: headers });
  }
}
