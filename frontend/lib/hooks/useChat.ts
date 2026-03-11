/**
 * Chat State Management Hook
 *
 * Manages chat state including messages, conversation ID, loading, and errors.
 * Handles message sending with JWT authentication.
 */

"use client";

import { useState, useCallback, useRef } from "react";
import { ChatMessage, ChatError, ChatRequest } from "@/lib/types/chat";
import { sendChatMessage } from "@/lib/api/chat-api";
import { useJwtToken } from "./useJwtToken";

interface UseChatOptions {
  userId: string;
  onUnauthorized?: () => void;
}

export function useChat({ userId, onUnauthorized }: UseChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ChatError | null>(null);
  const token = useJwtToken();

  // Track the last message to prevent duplicates
  const lastMessageRef = useRef<string>("");

  /**
   * Send a message to the chat agent
   */
  const sendMessage = useCallback(
    async (messageText: string) => {
      // Prevent duplicate sends
      if (messageText === lastMessageRef.current && isLoading) {
        console.log("[useChat] Duplicate send prevented");
        return;
      }

      if (!token) {
        console.error("[useChat] No token available");
        const authError: ChatError = {
          status: 401,
          message: "Not authenticated. Please sign in.",
          retryable: false,
        };
        setError(authError);
        onUnauthorized?.();
        return;
      }

      lastMessageRef.current = messageText;
      setIsLoading(true);
      setError(null);

      // Add user message to UI immediately (optimistic update)
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: messageText,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      try {
        const request: ChatRequest = {
          conversation_id: conversationId,
          message: messageText,
        };

        const response = await sendChatMessage(userId, request, token);

        // Update conversation ID if this is the first message
        if (conversationId === null) {
          setConversationId(response.conversation_id);
        }

        // Add assistant message to UI
        const assistantMessage: ChatMessage = {
          id: `assistant-${response.message_id}`,
          role: "assistant",
          content: response.content,
          timestamp: response.timestamp,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        const chatError = err as ChatError;
        setError(chatError);

        // Handle unauthorized errors
        if (chatError.status === 401) {
          onUnauthorized?.();
        }

        // Remove optimistic user message on error
        setMessages((prev) => prev.filter((msg) => msg.id !== userMessage.id));
      } finally {
        setIsLoading(false);
        lastMessageRef.current = "";
      }
    },
    [userId, token, conversationId, isLoading, onUnauthorized]
  );

  /**
   * Retry the last failed message
   */
  const retry = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Clear error
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Reset conversation (clear messages and conversation ID)
   */
  const resetConversation = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    messages,
    conversationId,
    isLoading,
    error,
    sendMessage,
    retry,
    clearError,
    resetConversation,
  };
}
