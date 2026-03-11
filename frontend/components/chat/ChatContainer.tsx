/**
 * ChatContainer Component
 *
 * Main chat UI container that integrates all chat components.
 * Manages chat state and user interactions.
 */

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import { useChat } from "@/lib/hooks/useChat";
import { GlassCard } from "@/components/ui/GlassCard";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { LoadingIndicator } from "./LoadingIndicator";
import { ErrorMessage } from "./ErrorMessage";

export function ChatContainer() {
  const { session } = useAuth();
  const router = useRouter();

  const userId = session?.user?.id?.toString();

  const {
    messages,
    conversationId,
    isLoading,
    error,
    sendMessage,
    retry,
    clearError,
    resetConversation,
  } = useChat({
    userId: userId || "",
    onUnauthorized: () => {
      router.push("/signin");
    },
  });

  // Reset conversation on mount (fresh start)
  useEffect(() => {
    resetConversation();
  }, [resetConversation]);

  const handleSendMessage = (message: string) => {
    sendMessage(message);
  };

  const handleRetry = () => {
    clearError();
    // User can type a new message after clearing error
  };

  return (
    <GlassCard padding="none" className="flex flex-col h-full">
      {/* Chat header */}
      <div className="px-6 py-4 border-b border-white/10">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">AI Assistant</h2>
            <p className="text-sm text-gray-400">
              {conversationId
                ? `Conversation #${conversationId}`
                : "Start a new conversation"}
            </p>
          </div>
          {messages.length > 0 && (
            <button
              onClick={resetConversation}
              className="text-sm text-gray-400 hover:text-cyan-400 transition-colors"
              aria-label="Start new conversation"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Message list */}
      <MessageList messages={messages} />

      {/* Loading indicator */}
      {isLoading && <LoadingIndicator />}

      {/* Error message */}
      {error && (
        <ErrorMessage error={error} onRetry={handleRetry} onDismiss={clearError} />
      )}

      {/* Chat input */}
      <div className="px-4 py-4 border-t border-white/10">
        <ChatInput
          onSend={handleSendMessage}
          disabled={isLoading}
          placeholder="Type your message... (Enter to send)"
        />
      </div>
    </GlassCard>
  );
}
