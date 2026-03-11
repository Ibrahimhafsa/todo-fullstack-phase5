/**
 * Chat Type Definitions
 *
 * Defines TypeScript types for the chat functionality,
 * matching the Spec-4 backend API contract.
 */

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface ChatRequest {
  conversation_id: number | null;
  message: string;
}

export interface ChatResponse {
  message_id: number;
  conversation_id: number;
  role: "assistant";
  content: string;
  timestamp: string;
}

export interface ChatError {
  status: number;
  message: string;
  retryable: boolean;
}

export interface ChatState {
  messages: ChatMessage[];
  conversationId: number | null;
  isLoading: boolean;
  error: ChatError | null;
}
