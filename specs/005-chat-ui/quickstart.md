# Quickstart: Chat UI Integration Guide (SPEC-5)

**Feature**: Chat UI with OpenAI ChatKit
**Frontend**: Next.js 16 + React 19 + TypeScript
**Date**: 2026-02-20

## Prerequisites

- ✅ Node.js 18+ installed
- ✅ Frontend project already set up (`/frontend` directory)
- ✅ Better Auth integration working (authentication available)
- ✅ Backend chat endpoint available (`POST /api/{user_id}/chat`)
- ✅ Tailwind CSS configured (design system ready)

## Installation Steps

### Step 1: Install ChatKit Package

```bash
cd frontend
npm install @openai/chatkit
```

**Verify Installation**:
```bash
npm list @openai/chatkit
# Output: @openai/chatkit@X.Y.Z
```

### Step 2: Add Environment Variables

Create or update `.env.local`:

```env
# Existing
NEXT_PUBLIC_API_URL=http://localhost:8000

# New - ChatKit configuration
NEXT_PUBLIC_OPENAI_DOMAIN_KEY=your-domain-key-here
```

**For Production (Vercel)**:
- Set `NEXT_PUBLIC_OPENAI_DOMAIN_KEY` in Vercel dashboard
- Set `NEXT_PUBLIC_API_URL` to production API URL

### Step 3: Create Chat Page Structure

```bash
cd frontend

# Create route directory
mkdir -p app/(protected)/chat

# Create page component
touch app/(protected)/chat/page.tsx

# Create components directory
mkdir -p components/chat

# Create component files
touch components/chat/ChatContainer.tsx
touch components/chat/MessageList.tsx
touch components/chat/MessageBubble.tsx
touch components/chat/ChatInput.tsx
touch components/chat/LoadingIndicator.tsx
touch components/chat/ErrorMessage.tsx

# Create API client
touch lib/chat-client.ts

# Create hooks
mkdir -p lib/hooks
touch lib/hooks/useChat.ts
touch lib/hooks/useJWTToken.ts

# Create types
touch lib/types/chat.ts
```

### Step 4: Create Type Definitions

**File**: `frontend/lib/types/chat.ts`

```typescript
export interface Message {
  id: number;
  conversationId: number;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface Conversation {
  id: number;
  title?: string;
  createdAt: Date;
  messageCount: number;
}

export interface ChatRequest {
  conversation_id?: number | null;
  message: string;
}

export interface ChatResponse {
  message_id: number;
  conversation_id: number;
  role: string;
  content: string;
  timestamp: string;
}

export interface ChatUIState {
  conversationId: number | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  inputValue: string;
}
```

### Step 5: Create Chat API Client

**File**: `frontend/lib/chat-client.ts`

```typescript
import { ChatRequest, ChatResponse } from "./types/chat";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ChatAPIError extends Error {
  constructor(
    public status: number,
    public data: any
  ) {
    super(`Chat API Error: ${status}`);
  }
}

export async function sendChatMessage(
  token: string,
  userId: string,
  request: ChatRequest
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/${userId}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new ChatAPIError(res.status, data);
  }

  return res.json();
}

export async function listConversations(
  token: string,
  userId: string
): Promise<any[]> {
  const res = await fetch(`${API_URL}/api/${userId}/conversations`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) throw new ChatAPIError(res.status, await res.json());
  return res.json();
}

export async function deleteConversation(
  token: string,
  userId: string,
  conversationId: number
): Promise<void> {
  const res = await fetch(`${API_URL}/api/${userId}/conversations/${conversationId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) throw new ChatAPIError(res.status, await res.json());
}
```

### Step 6: Create Custom Hooks

**File**: `frontend/lib/hooks/useJWTToken.ts`

```typescript
import { useEffect, useState } from "react";

export function useJWTToken(): string | null {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check localStorage immediately
    const savedToken = localStorage.getItem("auth_token");
    setToken(savedToken);
    setIsLoading(false);

    // Listen for token changes
    const handleTokenChange = (e: any) => {
      setToken(e.detail?.token || null);
    };

    window.addEventListener("auth_token_changed", handleTokenChange);
    return () => window.removeEventListener("auth_token_changed", handleTokenChange);
  }, []);

  return token;
}

export function extractUserIdFromToken(token: string): string {
  try {
    // Decode JWT (simple base64 decode - no validation)
    const parts = token.split(".");
    if (parts.length !== 3) throw new Error("Invalid token format");

    const decoded = JSON.parse(atob(parts[1]));
    return decoded.sub || decoded.user_id || decoded.id || "";
  } catch (e) {
    console.error("Failed to extract user_id from token:", e);
    return "";
  }
}
```

**File**: `frontend/lib/hooks/useChat.ts`

```typescript
import { useCallback, useReducer } from "react";
import { ChatUIState, Message } from "../types/chat";
import { sendChatMessage, ChatAPIError } from "../chat-client";

type Action =
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "SET_ERROR"; payload: string | null }
  | { type: "SET_INPUT"; payload: string }
  | { type: "ADD_MESSAGE"; payload: Message }
  | { type: "SET_CONVERSATION"; payload: number }
  | { type: "RESET" };

const initialState: ChatUIState = {
  conversationId: null,
  messages: [],
  isLoading: false,
  error: null,
  inputValue: "",
};

function reducer(state: ChatUIState, action: Action): ChatUIState {
  switch (action.type) {
    case "SET_LOADING":
      return { ...state, isLoading: action.payload };
    case "SET_ERROR":
      return { ...state, error: action.payload };
    case "SET_INPUT":
      return { ...state, inputValue: action.payload };
    case "ADD_MESSAGE":
      return { ...state, messages: [...state.messages, action.payload] };
    case "SET_CONVERSATION":
      return { ...state, conversationId: action.payload };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

export function useChat(token: string | null, userId: string | null) {
  const [state, dispatch] = useReducer(reducer, initialState);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!token || !userId) {
        dispatch({ type: "SET_ERROR", payload: "Not authenticated" });
        return;
      }

      const trimmed = text.trim();
      if (!trimmed) {
        dispatch({ type: "SET_ERROR", payload: "Message cannot be empty" });
        return;
      }

      dispatch({ type: "SET_LOADING", payload: true });
      dispatch({ type: "SET_ERROR", payload: null });

      try {
        // Send user message to backend
        const response = await sendChatMessage(token, userId, {
          conversation_id: state.conversationId,
          message: trimmed,
        });

        // Update conversation ID
        if (response.conversation_id) {
          dispatch({ type: "SET_CONVERSATION", payload: response.conversation_id });
        }

        // Add assistant message
        dispatch({
          type: "ADD_MESSAGE",
          payload: {
            id: response.message_id,
            conversationId: response.conversation_id,
            role: "assistant",
            content: response.content,
            timestamp: new Date(response.timestamp),
          },
        });

        // Clear input
        dispatch({ type: "SET_INPUT", payload: "" });
      } catch (error) {
        let errorMessage = "Failed to send message";

        if (error instanceof ChatAPIError) {
          if (error.status === 429) {
            errorMessage = "You're sending messages too fast. Please wait a moment.";
          } else if (error.status === 503) {
            errorMessage = "Chat service is temporarily unavailable. Please try again.";
          } else if (error.status === 401) {
            errorMessage = "Your session expired. Please sign in again.";
          } else if (error.status === 400) {
            errorMessage = "Invalid message. Please check and try again.";
          }
        }

        dispatch({ type: "SET_ERROR", payload: errorMessage });
      } finally {
        dispatch({ type: "SET_LOADING", payload: false });
      }
    },
    [token, userId, state.conversationId]
  );

  const reset = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  return { state, sendMessage, reset, dispatch };
}
```

### Step 7: Create UI Components

**File**: `frontend/components/chat/MessageBubble.tsx`

```typescript
import { Message } from "@/lib/types/chat";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`
          max-w-xs rounded-lg px-4 py-2 whitespace-pre-wrap break-words
          ${isUser
            ? "bg-cyan-500/20 text-right text-white"
            : "bg-teal-500/20 text-left text-white"
          }
        `}
      >
        <p>{message.content}</p>
        <span className="text-xs text-gray-400 mt-1 block">
          {message.timestamp.toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}
```

**File**: `frontend/components/chat/ChatInput.tsx`

```typescript
import { useState } from "react";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export function ChatInput({ onSendMessage, isLoading }: ChatInputProps) {
  const [text, setText] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim()) {
      onSendMessage(text);
      setText("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-4 border-t border-cyan-500/30">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
        disabled={isLoading}
        rows={3}
        className="flex-1 bg-black/30 border border-cyan-500/30 rounded-lg p-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
      />
      <button
        type="submit"
        disabled={isLoading}
        className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 disabled:opacity-50 rounded-lg text-white font-medium transition"
      >
        {isLoading ? "..." : "Send"}
      </button>
    </form>
  );
}
```

**File**: `frontend/components/chat/ChatContainer.tsx`

```typescript
import { useEffect, useRef } from "react";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { useChat } from "@/lib/hooks/useChat";

interface ChatContainerProps {
  token: string | null;
  userId: string | null;
}

export function ChatContainer({ token, userId }: ChatContainerProps) {
  const { state, sendMessage } = useChat(token, userId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [state.messages]);

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {state.messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p>No messages yet. Start a conversation!</p>
          </div>
        )}
        {state.messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {state.isLoading && (
          <div className="text-center">
            <p className="text-gray-400">AI is thinking...</p>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Error */}
      {state.error && (
        <div className="bg-red-500/20 border border-red-500 p-3 mx-4 rounded text-red-200 text-sm">
          {state.error}
        </div>
      )}

      {/* Input */}
      <ChatInput onSendMessage={sendMessage} isLoading={state.isLoading} />
    </div>
  );
}
```

**File**: `frontend/app/(protected)/chat/page.tsx`

```typescript
"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ChatContainer } from "@/components/chat/ChatContainer";
import { useJWTToken, extractUserIdFromToken } from "@/lib/hooks/useJWTToken";

export default function ChatPage() {
  const router = useRouter();
  const token = useJWTToken();
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      router.push("/signin");
      return;
    }

    const uid = extractUserIdFromToken(token);
    if (!uid) {
      console.error("Could not extract user ID from token");
      router.push("/signin");
      return;
    }

    setUserId(uid);
  }, [token, router]);

  if (!token || !userId) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return (
    <div className="flex flex-col h-screen bg-black text-white">
      <header className="border-b border-cyan-500/30 p-4">
        <h1 className="text-2xl font-bold">Chat with AI</h1>
      </header>
      <main className="flex-1 flex">
        <ChatContainer token={token} userId={userId} />
      </main>
    </div>
  );
}
```

## Testing

### Manual Testing Checklist

- [ ] Navigate to `/chat` (should load chat page)
- [ ] Send a test message (should appear in chat)
- [ ] Wait for response (should display assistant message)
- [ ] Check browser DevTools → Network (should include JWT in Authorization header)
- [ ] Test on mobile (responsive design)
- [ ] Test error handling (disconnect backend, verify error message)
- [ ] Test rate limiting (send 25 messages rapidly, verify 429 response)
- [ ] Test logout (conversation should reset on next login)

### Test Cases

**TC-001: Send Message**
1. Login and navigate to `/chat`
2. Type a message: "Hello"
3. Click Send
4. Expected: Message appears in chat, spinner shows, response appears

**TC-002: Multi-turn Conversation**
1. Send message 1: "Create a task"
2. Wait for response
3. Send message 2: "Add another"
4. Expected: Both messages reference same `conversation_id`, context maintained

**TC-003: Error Handling**
1. Disconnect backend
2. Send a message
3. Expected: Error message displays, retry button available

**TC-004: Mobile Responsiveness**
1. Open DevTools → Device Toolbar
2. Select iPhone 12 (390px width)
3. Send message
4. Expected: Input at bottom, messages readable, no horizontal scroll

## Deployment to Vercel

### Environment Variables

Set in Vercel project dashboard:

```
NEXT_PUBLIC_OPENAI_DOMAIN_KEY=prod-key-12345
NEXT_PUBLIC_API_URL=https://api.production.com
```

### Build & Deploy

```bash
git add .
git commit -m "feat: add chat UI with OpenAI ChatKit"
git push origin 005-chat-ui

# Vercel will auto-deploy on push
# Check deployment: https://your-project.vercel.app
```

### Post-Deployment Verification

- [ ] `/chat` route loads successfully
- [ ] Chat API calls succeed (check browser DevTools)
- [ ] Messages send and receive correctly
- [ ] No console errors
- [ ] Mobile responsive (iOS Safari, Android Chrome)