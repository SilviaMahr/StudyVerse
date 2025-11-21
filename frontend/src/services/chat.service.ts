import {Injectable} from '@angular/core';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {AuthService} from './auth.service';
import {Observable, timeout} from 'rxjs';
import {
  ChatSendRequest,
  ChatSendResponse,
  ChatHistoryResponse,
  ChatMessage
} from '../app/models/chat.model';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private baseUrl = 'http://127.0.0.1:8000/chat';

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) {}

  /**
   * Sends a message to the LLM and returns the response
   */
  public sendMessage(message: string, planningId?: number): Observable<ChatSendResponse> {
    const token = this.authService.getToken();

    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    });

    const body: ChatSendRequest = { message };

    const url = planningId
      ? `${this.baseUrl}/send?planning_id=${planningId}`
      : `${this.baseUrl}/send`;

    // Add 60 second timeout for LLM response
    return this.http.post<ChatSendResponse>(url, body, { headers }).pipe(
      timeout(60000)
    );
  }

  /**
   * Retrieves chat history for a specific planning session
   */
  public getChatHistory(planningId: number, limit: number = 50): Observable<ChatHistoryResponse> {
    const token = this.authService.getToken();

    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    });

    const url = `${this.baseUrl}/history/${planningId}`;

    return this.http.get<ChatHistoryResponse>(url, {
      headers,
      params: { limit: limit.toString() }
    });
  }
}
