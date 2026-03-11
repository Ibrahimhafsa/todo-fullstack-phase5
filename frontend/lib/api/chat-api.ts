/**
 * Chat API Client
 *
 * Handles communication with the Spec-4 backend agent endpoint.
 * Implements JWT authentication and error handling.
 */

import { ChatRequest, ChatResponse, ChatError } from "@/lib/types/chat";

const API =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://todo-backend-phase3-ec30.onrender.com";

/**
 * Send a chat message to the backend agent
 *
 * @param userId - User ID from JWT claims
 * @param request - Chat request payload (conversation_id, message)
 * @param token - JWT token for authentication
 * @returns ChatResponse from backend
 * @throws ChatError on failure
 */
export async function sendChatMessage(
  userId: string,
  request: ChatRequest,
  token: string
): Promise<ChatResponse> {
  try {
    console.log("[sendChatMessage] Sending to:", `${API}/api/${userId}/chat`);
    console.log("[sendChatMessage] Request:", request);

    const response = await fetch(`${API}/api/${userId}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(request),
    });

    console.log("[sendChatMessage] Response status:", response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: response.statusText,
      }));

      const error: ChatError = {
        status: response.status,
        message: errorData.detail || getErrorMessage(response.status),
        retryable: isRetryable(response.status),
      };

      console.error("[sendChatMessage] Error:", error);
      throw error;
    }

    const data: ChatResponse = await response.json();
    console.log("[sendChatMessage] Success:", data);
    return data;
  } catch (error) {
    console.error("[sendChatMessage] Fetch error:", error);

    // If error is already a ChatError, rethrow it
    if (isTypedChatError(error)) {
      throw error;
    }

    // Network or unexpected error
    const chatError: ChatError = {
      status: 0,
      message: "Network error. Please check your connection and try again.",
      retryable: true,
    };
    throw chatError;
  }
}

/**
 * Get user-friendly error message based on status code
 */
function getErrorMessage(status: number): string {
  switch (status) {
    case 400:
      return "Invalid request. Please check your message and try again.";
    case 401:
      return "Your session has expired. Please sign in again.";
    case 404:
      return "Chat service not found. Please contact support.";
    case 429:
      return "Too many requests. Please wait a moment and try again.";
    case 503:
      return "Chat service is temporarily unavailable. Please try again later.";
    default:
      return `An error occurred (${status}). Please try again.`;
  }
}

/**
 * Determine if an error is retryable
 */
function isRetryable(status: number): boolean {
  // Retryable: network errors, rate limits, service unavailable
  // Not retryable: bad request, unauthorized, not found
  return status === 0 || status === 429 || status === 503;
}

/**
 * Type guard for ChatError
 */
function isTypedChatError(error: unknown): error is ChatError {
  return (
    typeof error === "object" &&
    error !== null &&
    "status" in error &&
    "message" in error &&
    "retryable" in error
  );
}
