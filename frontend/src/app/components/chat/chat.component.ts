import {CommonModule} from '@angular/common';
import {FormsModule, NgForm} from '@angular/forms';
import {Component, OnInit} from '@angular/core';
import {PlanningStateService} from '../../../services/planning-state.service';
import {ChatService} from '../../../services/chat.service';

interface ChatMessage {
  sender: 'user' | 'UNI';
  text: string;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit {
  messages: ChatMessage[] = [];
  currentMessage: string = '';

  isLLMLoading: boolean = false;
  currentPlanningId: number | null = null;

  constructor(
    private planningState: PlanningStateService,
    private chatService: ChatService
  ) { }

  ngOnInit() {
    this.messages.push({
      sender: 'UNI',
      text: "Hallo! Ich bin UNI, dein Planungsassistent. Sag mir, wie ich diesen Plan anpassen kann."
    });

    // Subscribe to current planning to get the planning ID
    this.planningState.planning$.subscribe({
      next: (planning) => {
        this.currentPlanningId = planning?.id ?? null;
        console.log('Current planning ID:', this.currentPlanningId);
      }
    });
  }

  onSendMessage(chatForm: NgForm): void{
    if (!chatForm.value.message) return;

    const userMessage: ChatMessage = {
      sender: 'user',
      text: chatForm.value.message
    };

    this.messages.push(userMessage);

    // Send message to LLM
    this.isLLMLoading = true;
    this.sendMessageToLLM(chatForm.value.message);
    // OLD CODE: this.addDummyLLMResponse(chatForm.value.message);

    chatForm.reset();
  }

  private sendMessageToLLM(userText: string): void {
    console.log('Sending message to LLM:', userText);
    console.log('With planning ID:', this.currentPlanningId);

    this.chatService.sendMessage(userText, this.currentPlanningId ?? undefined).subscribe({
      next: (response) => {

        setTimeout(() => {
          console.log('LLM Response received:', response);
          this.isLLMLoading = false;
          this.messages.push({
            sender: 'UNI',
            text: response.message
          });
        }, 0);
      },
      error: (error) => {
        setTimeout(() => {
          console.error('Error sending message to LLM:', error);
          console.error('Error status:', error.status);
          console.error('Error message:', error.message);
          this.isLLMLoading = false;
          this.messages.push({
            sender: 'UNI',
            text: 'Entschuldigung, es gab einen Fehler bei der Verarbeitung deiner Nachricht. Bitte versuche es erneut.'
          });
        },0);
      }
    });
  }

  // ========== OLD DUMMY CODE (kept for reference) ==========
  // private addDummyLLMResponse(userText: string): void {
  //   setTimeout(() => {
  //     this.isLLMLoading = false;
  //     this.messages.push({
  //       sender: 'UNI',
  //       text: `Okay, ich habe deine Anmerkung "${userText}" zur Kenntnis genommen.`
  //     });
  //   }, 500);
  // }

  closeChat(): void {
    this.planningState.closeChat();
  }
}
