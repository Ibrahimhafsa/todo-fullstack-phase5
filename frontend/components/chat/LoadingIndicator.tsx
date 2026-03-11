/**
 * LoadingIndicator Component
 *
 * Shows a typing indicator when the assistant is generating a response.
 */

"use client";

export function LoadingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[80%] sm:max-w-[70%] rounded-2xl px-4 py-3 bg-white/10 backdrop-blur-md border border-white/20 shadow-lg">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
          </div>
          <span className="text-sm text-gray-400">AI is thinking...</span>
        </div>
      </div>
    </div>
  );
}
