/**
 * MessageBubble Component
 *
 * Displays a single message in the chat UI.
 * Supports user and assistant roles with distinct styling.
 */

"use client";

import { ChatMessage } from "@/lib/types/chat";

export interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4 animate-fadeIn`}
    >
      <div
        className={`
          max-w-[80%] sm:max-w-[70%] rounded-2xl px-4 py-3
          ${
            isUser
              ? "bg-cyan-500 text-black ml-auto"
              : "bg-white/10 backdrop-blur-md text-white border border-white/20"
          }
          shadow-lg
        `.trim()}
      >
        {/* Message content */}
        <p className="text-sm sm:text-base leading-relaxed whitespace-pre-wrap break-words">
          {message.content}
        </p>

        {/* Timestamp */}
        <p
          className={`
            text-xs mt-2
            ${isUser ? "text-black/60" : "text-gray-400"}
          `.trim()}
        >
          {formatTimestamp(message.timestamp)}
        </p>
      </div>
    </div>
  );
}

/**
 * Format timestamp to a human-readable format
 */
function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    // Show time for today's messages
    const isToday = date.toDateString() === now.toDateString();
    if (isToday) {
      return date.toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "2-digit",
      });
    }

    // Show date for older messages
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  } catch {
    return "";
  }
}
