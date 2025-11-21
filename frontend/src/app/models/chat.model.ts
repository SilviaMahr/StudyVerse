/**
 * Chat-related models for the StudyVerse application
 */

/**
 * Request payload for sending a chat message
 */
export interface ChatSendRequest {
  message: string;
}

/**
 * Response from sending a chat message
 */
export interface ChatSendResponse {
  success: boolean;
  message: string;
  timestamp: string;
  user_message_id?: number;
  assistant_message_id?: number;
}

/**
 * A single chat message
 * - role 'user' represents the user
 * - role 'assistant' represents UNI (the chatbot)
 */
export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

/**
 * Response containing chat history for a planning session
 */
export interface ChatHistoryResponse {
  planning_id: number;
  messages: ChatMessage[];
  total: number;
}
