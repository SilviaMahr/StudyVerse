import {Injectable} from '@angular/core';
import {HttpClient, HttpHeaders, HttpParams} from '@angular/common/http';
@Injectable({
  providedIn: 'root'
})
export class APILoginService {
  private api_url = 'http://127.0.0.1:8000/auth/login';
  data: string[] = [];

  constructor(private http: HttpClient) {}

  http_headers = {
    headers: new HttpHeaders({
      'Content-Type': 'application/json',
    })
  }

  login(email: string, pw: string) {
    const body = new HttpParams()
      .set('username', email)
      .set('password', pw);
    return this.http.post(
      this.api_url,
      body.toString(),
      {
        headers: new HttpHeaders({
          'Content-Type': 'application/x-www-form-urlencoded'
        })
      }
    );
  }
}
