import {CommonModule} from '@angular/common';
import {FormsModule, NgForm} from '@angular/forms';
import {ChangeDetectorRef, Component, OnInit} from '@angular/core';
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
    private chatService: ChatService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    // Subscribe to current planning to get the planning ID and load chat history
    this.planningState.planning$.subscribe({
      next: (planning) => {
        this.currentPlanningId = planning?.id ?? null;
        console.log('Current planning ID:', this.currentPlanningId);

        // Load chat history when planning ID is available
        if (this.currentPlanningId !== null) {
          this.loadChatHistory(this.currentPlanningId);
        } else {
          // Show welcome message if no planning ID
          this.messages = [{
            sender: 'UNI',
            text: "Hallo! Ich bin UNI, dein Planungsassistent. Sag mir, wie ich diesen Plan anpassen kann."
          }];
        }
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
          console.log('LLM Response received:', response);
          this.isLLMLoading = false;
          this.messages.push({
            sender: 'UNI',
            text: response.message
          });
          this.cdr.detectChanges();
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
          this.cdr.detectChanges();
      }
    });
  }

  private loadChatHistory(planningId: number): void {
    console.log('Loading chat history for planning ID:', planningId);

    this.chatService.getChatHistory(planningId).subscribe({
      next: (response) => {
        console.log('Chat history loaded:', response);

        // Convert API messages to component format
        this.messages = response.messages.map(msg => ({
          sender: msg.role === 'user' ? 'user' : 'UNI',
          text: msg.content
        }));

        // If no messages exist, show welcome message
        if (this.messages.length === 0) {
          this.messages.push({
            sender: 'UNI',
            text: "Hallo! Ich bin UNI, dein Planungsassistent. Sag mir, wie ich diesen Plan anpassen kann."
          });
        }

        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error loading chat history:', error);
        // Show welcome message on error
        this.messages = [{
          sender: 'UNI',
          text: "Hallo! Ich bin UNI, dein Planungsassistent. Sag mir, wie ich diesen Plan anpassen kann."
        }];
        this.cdr.detectChanges();
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
