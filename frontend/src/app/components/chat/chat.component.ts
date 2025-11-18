import {CommonModule} from '@angular/common';
import {FormsModule, NgForm} from '@angular/forms';
import {Component, OnInit} from '@angular/core';
import {PlanningStateService} from '../../../services/planning-state.service';

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

  constructor(private planningState: PlanningStateService) { }

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

    //TODO send message to LLM
    this.isLLMLoading = true;
    this.addDummyLLMResponse(chatForm.value.message);

    chatForm.reset();
  }
//dummy-code for testing
  private addDummyLLMResponse(userText: string): void {
    setTimeout(() => {
      this.isLLMLoading = false;
      this.messages.push({
        sender: 'UNI',
        text: `Okay, ich habe deine Anmerkung "${userText}" zur Kenntnis genommen.`
      });
    }, 500);
  }

  closeChat(): void {
    this.planningState.closeChat();
  }
}
