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

  constructor(
    private planningState: PlanningStateService,
    private chatService: ChatService
  ) { }

  ngOnInit() {
    this.messages.push({
      sender: 'UNI',
      text: "Hallo! Ich bin UNI, dein Planungsassistent. Sag mir, wie ich diesen Plan anpassen kann."
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

    this.chatService.sendMessage(userText).subscribe({
      next: (response) => {
        console.log('LLM Response received:', response);
        this.isLLMLoading = false;
        this.messages.push({
          sender: 'UNI',
          text: response.message
        });
      },
      error: (error) => {
        console.error('Error sending message to LLM:', error);
        console.error('Error status:', error.status);
        console.error('Error message:', error.message);
        this.isLLMLoading = false;
        this.messages.push({
          sender: 'UNI',
          text: 'Entschuldigung, es gab einen Fehler bei der Verarbeitung deiner Nachricht. Bitte versuche es erneut.'
        });
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
