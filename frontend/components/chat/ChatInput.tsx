/**
 * ChatInput Component
 *
 * Input field for typing and sending messages.
 * Includes send button and keyboard shortcuts (Enter to send).
 */

"use client";

import { useState, FormEvent, KeyboardEvent } from "react";
import { Button } from "@/components/ui/Button";

export interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Type your message...",
}: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (trimmed && !disabled) {
      onSend(trimmed);
      setInput("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2">
      {/* Message input */}
      <div className="flex-1 relative">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="
            w-full px-4 py-3 pr-12
            bg-white/5 backdrop-blur-md
            border border-white/20 rounded-xl
            text-white placeholder-gray-400
            focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50
            disabled:opacity-50 disabled:cursor-not-allowed
            resize-none
            transition-all duration-200
            min-h-[48px] max-h-[120px]
          "
          style={{
            height: "auto",
            overflowY: input.split("\n").length > 3 ? "auto" : "hidden",
          }}
        />
        {/* Character count hint (optional) */}
        {input.length > 0 && (
          <div className="absolute bottom-2 right-3 text-xs text-gray-500">
            {input.length}
          </div>
        )}
      </div>

      {/* Send button */}
      <Button
        type="submit"
        disabled={disabled || !input.trim()}
        size="md"
        variant="primary"
        className="min-w-[48px] h-[48px] px-4"
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
            d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
          />
        </svg>
      </Button>
    </form>
  );
}
