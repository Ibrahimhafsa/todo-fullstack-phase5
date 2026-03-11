/**
 * ErrorMessage Component
 *
 * Displays error messages with retry capability.
 */

"use client";

import { ChatError } from "@/lib/types/chat";
import { Button } from "@/components/ui/Button";

export interface ErrorMessageProps {
  error: ChatError;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export function ErrorMessage({ error, onRetry, onDismiss }: ErrorMessageProps) {
  return (
    <div className="px-4 mb-4">
      <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 backdrop-blur-md">
        <div className="flex items-start gap-3">
          {/* Error icon */}
          <div className="flex-shrink-0 w-6 h-6 mt-0.5">
            <svg
              className="w-6 h-6 text-red-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>

          {/* Error content */}
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-red-400 mb-1">
              Message failed to send
            </h4>
            <p className="text-sm text-red-300/90">{error.message}</p>

            {/* Action buttons */}
            <div className="flex gap-2 mt-3">
              {error.retryable && onRetry && (
                <Button size="sm" variant="secondary" onClick={onRetry}>
                  Try Again
                </Button>
              )}
              {onDismiss && (
                <Button size="sm" variant="ghost" onClick={onDismiss}>
                  Dismiss
                </Button>
              )}
            </div>
          </div>

          {/* Close button */}
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="flex-shrink-0 w-5 h-5 text-red-400 hover:text-red-300 transition-colors"
              aria-label="Dismiss error"
            >
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
