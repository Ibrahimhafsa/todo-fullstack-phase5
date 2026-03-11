# Data Model & Component Design: Chat UI (SPEC-5)

**Feature**: Chat UI with OpenAI ChatKit
**Phase**: Phase 1 Design
**Date**: 2026-02-20

## Frontend Data Model

All data is transient (no persistence). Chat state stored in React state only per Constitutional Principle XVII.

### Core Entities

#### Message

Represents a single message in the conversation.

```typescript
interface Message {
  id: number;                    // Unique message ID (from backend)
  conversationId: number;        // Reference to conversation
  role: "user" | "assistant";   // Message author
  content: string;               // Message text (supports multi-line)
  timestamp: Date;               // When message was sent
  error?: string;                // Optional error state (client-side)
  isLoading?: boolean;           // Optional loading indicator (pending response)
}
```

**Validation Rules**:
- `id`: Must be positive integer (from backend)
- `conversationId`: Must be positive integer
- `role`: Enum of "user" or "assistant"
- `content`: Must be non-empty string, max 10,000 characters
- `timestamp`: ISO 8601 format, server-provided

**State Transitions**:
```
[LOCAL] → SENDING (isLoading=true) → SENT (timestamp set) → RECEIVED (backend acks)
[ERROR] → RETRY (isLoading=true) → SENT
```

---

#### Conversation

Represents a chat session. Only the `id` is actively managed; other fields are informational.

```typescript
interface Conversation {
  id: number;                    // Unique conversation ID (from backend)
  title?: string;                // Optional human-readable title
  createdAt: Date;               // When conversation started
  updatedAt?: Date;              // Last activity
  messageCount: number;          // Cached message count
  userId: string;                // Implicit (from JWT) - not stored in state
}
```

**Validation Rules**:
- `id`: Must be positive integer
- `title`: Optional, max 255 characters
- `createdAt`: ISO 8601 format
- `messageCount`: Non-negative integer

**Lifecycle**:
- Created: On first message send (null → `id` from backend response)
- Maintained: For subsequent messages in same conversation
- Reset: On logout or user navigates away (back to null)

---

#### ChatUIState

Top-level state for chat page component.

```typescript
interface ChatUIState {
  // Conversation tracking
  conversationId: number | null;
  messages: Message[];

  // UI states
  isLoading: boolean;           // True while waiting for response
  error: string | null;         // Error message to display

  // User input
  inputValue: string;           // Current draft message

  // Metadata
  lastUpdated: Date;            // For sorting/rendering optimization
  messageCount: number;         // Cached count (optimization)
}
```

**Initial State**:
```typescript
{
  conversationId: null,
  messages: [],
  isLoading: false,
  error: null,
  inputValue: "",
  lastUpdated: new Date(),
  messageCount: 0,
}
```

---

### Request/Response Models (API Contracts)

#### ChatRequest

Sent to backend when user sends a message.

```typescript
interface ChatRequest {
  conversation_id?: number | null;  // Null for new conversation
  message: string;                   // User message
}

// Example:
{
  conversation_id: null,  // First message
  message: "Help me organize my tasks"
}

// Example (subsequent):
{
  conversation_id: 42,
  message: "Can you add 3 more items?"
}
```

**Validation**:
- `message`: Required, non-empty, max 10,000 characters
- `conversation_id`: Optional; if provided, must match current conversation

**Error Cases**:
- Empty message → 400 Bad Request
- Message > 10,000 chars → 400 Bad Request
- Invalid conversation_id → 404 Not Found
- User doesn't own conversation → 401 Unauthorized

---

#### ChatResponse

Returned by backend after processing message.

```typescript
interface ChatResponse {
  message_id: number;              // ID of assistant's response message
  conversation_id: number;         // Conversation this message belongs to
  role: "assistant";               // Always "assistant"
  content: string;                 // Assistant's response
  timestamp: string;               // ISO 8601 timestamp from server
}

// Example:
{
  message_id: 145,
  conversation_id: 42,
  role: "assistant",
  content: "I can help you manage your tasks. Here are 3 suggestions:\n1. Create a project list...",
  timestamp: "2026-02-20T14:32:15Z"
}
```

**Validation**:
- All fields required (non-null)
- `content`: Supports newlines and markdown-like formatting
- `timestamp`: Must be valid ISO 8601 date

**Error Responses**:
| Status | Response | Meaning |
|--------|----------|---------|
| 400 | `{ detail: "Message cannot be empty" }` | Invalid input |
| 401 | `{ detail: "User ID mismatch" }` | JWT doesn't match path |
| 404 | `{ detail: "Conversation not found" }` | Conversation doesn't exist or not owned |
| 429 | `{ detail: "Rate limit exceeded: max 20 requests per minute" }` | Too many requests |
| 503 | `{ detail: "Chat service temporarily unavailable" }` | OpenAI API down |

---

#### ConversationSummary

Used in conversation list.

```typescript
interface ConversationSummary {
  id: number;
  title?: string;
  created_at: string;        // ISO 8601
  message_count: number;     // Number of messages in this conversation
}
```

---

## Component Architecture

### Component Hierarchy

```
ChatPage (Route)
│
├── [AuthGuard - useJWTToken]
│
├── ChatContainer (Main wrapper)
│   ├── MessageList
│   │   ├── MessageBubble (x N)
│   │   │   ├── MessageContent (user or assistant)
│   │   │   └── Timestamp
│   │   └── EmptyState (if no messages)
│   │
│   ├── ChatInput
│   │   ├── TextArea (input field)
│   │   └── SendButton
│   │
│   ├── LoadingIndicator (if isLoading)
│   │   └── Spinner or TypingAnimation
│   │
│   └── ErrorMessage (if error)
│       ├── ErrorText
│       └── RetryButton
```

---

### Component Specifications

#### ChatPage (Route Component)

**Location**: `frontend/app/(protected)/chat/page.tsx`

**Props**: None (route-based)

**State**: Manages top-level ChatUIState

**Responsibilities**:
- Render chat container
- Manage conversation lifecycle
- Handle logout / session reset
- Fetch initial state if conversation exists

**Pseudo-code**:
```typescript
export default function ChatPage() {
  const [state, setState] = useState<ChatUIState>(initialState);
  const router = useRouter();

  // Get JWT token
  const token = useJWTToken();

  // Redirect to signin if no token
  useEffect(() => {
    if (!token) router.push("/signin");
  }, [token]);

  // Reset conversation on logout
  useEffect(() => {
    return () => {
      // Cleanup on unmount (logout detected)
      setState(prev => ({ ...prev, conversationId: null, messages: [] }));
    };
  }, []);

  return (
    <div className="flex flex-col h-screen">
      <ChatContainer state={state} setState={setState} token={token} />
    </div>
  );
}
```

---

#### ChatContainer (Wrapper Component)

**Location**: `frontend/components/chat/ChatContainer.tsx`

**Props**:
```typescript
interface ChatContainerProps {
  state: ChatUIState;
  setState: Dispatch<SetStateAction<ChatUIState>>;
  token: string;  // JWT token
}
```

**Responsibilities**:
- Render message list
- Render input form
- Call chat API on message send
- Manage loading/error states
- Scroll to latest message

**Key Methods**:
- `handleSendMessage(text: string)`: Send message to backend
- `handleRetry()`: Retry failed message
- `scrollToBottom()`: Auto-scroll message list

**Pseudo-code**:
```typescript
export function ChatContainer({ state, setState, token }: ChatContainerProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleSendMessage = async (text: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await sendChatMessage(
        token,
        { conversation_id: state.conversationId, message: text }
      );

      // Add user message
      const userMsg: Message = {
        id: Date.now(), // Temporary ID (will be replaced)
        conversationId: response.conversation_id,
        role: "user",
        content: text,
        timestamp: new Date(),
      };

      // Add assistant message
      const assistantMsg: Message = {
        id: response.message_id,
        conversationId: response.conversation_id,
        role: "assistant",
        content: response.content,
        timestamp: new Date(response.timestamp),
      };

      setState(prev => ({
        ...prev,
        conversationId: response.conversation_id,
        messages: [...prev.messages, userMsg, assistantMsg],
        inputValue: "",
        isLoading: false,
      }));

      scrollToBottom();
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: formatErrorMessage(error),
        isLoading: false,
      }));
    }
  };

  return (
    <div className="flex flex-col h-full gap-4">
      <MessageList messages={state.messages} />
      {state.isLoading && <LoadingIndicator />}
      {state.error && <ErrorMessage error={state.error} onRetry={handleRetry} />}
      <ChatInput onSendMessage={handleSendMessage} isLoading={state.isLoading} />
      <div ref={messagesEndRef} />
    </div>
  );
}
```

---

#### MessageList (Message Container)

**Location**: `frontend/components/chat/MessageList.tsx`

**Props**:
```typescript
interface MessageListProps {
  messages: Message[];
}
```

**Responsibilities**:
- Display all messages in chronological order
- Show empty state if no messages
- Auto-scroll on new messages
- Support message virtualization for large lists (optional)

**Key Methods**:
- `renderMessages()`: Map messages to MessageBubble components

---

#### MessageBubble (Message Component)

**Location**: `frontend/components/chat/MessageBubble.tsx`

**Props**:
```typescript
interface MessageBubbleProps {
  message: Message;
}
```

**Styling**:
- User messages: Right-aligned, accent color (cyan)
- Assistant messages: Left-aligned, primary color (teal)
- Use GlassCard for semi-transparent background
- Rounded corners (rounded-lg)
- Padding: consistent with design system

**Content Rendering**:
- Support multi-line text
- Preserve newlines
- Optional: Markdown rendering (if needed)
- Timestamp below content (small, muted text)

---

#### ChatInput (Input Component)

**Location**: `frontend/components/chat/ChatInput.tsx`

**Props**:
```typescript
interface ChatInputProps {
  onSendMessage: (text: string) => void;
  isLoading: boolean;  // Disable input while loading
}
```

**Responsibilities**:
- Text input field (multiline)
- Send button
- Validation (non-empty message)
- Clear input on send
- Disable while loading

**Keyboard Handling**:
- Enter: Send message
- Shift+Enter: New line
- Mobile: Show native keyboard

---

#### LoadingIndicator (Loading State)

**Location**: `frontend/components/chat/LoadingIndicator.tsx`

**Display**:
- Spinner animation (or dots animation)
- Text: "AI is thinking..." or "Typing..."
- Optional: Typing animation (simulated)

---

#### ErrorMessage (Error State)

**Location**: `frontend/components/chat/ErrorMessage.tsx`

**Props**:
```typescript
interface ErrorMessageProps {
  error: string;
  onRetry?: () => void;
}
```

**Display**:
- Error text (user-friendly, not technical)
- Retry button (if applicable)
- Dismiss button (clears error)

**Error Messages**:
- Rate limit: "You're sending messages too fast. Please wait a moment."
- Service down: "Chat service is temporarily unavailable. Please try again."
- Network: "Connection error. Please check your internet and try again."
- Auth: "Your session expired. Please sign in again."

---

## Custom Hooks

### useChat

Encapsulates chat logic and state management.

```typescript
interface UseChatReturn {
  state: ChatUIState;
  setState: Dispatch<SetStateAction<ChatUIState>>;
  sendMessage: (text: string) => Promise<void>;
  retry: () => Promise<void>;
  resetConversation: () => void;
}

export function useChat(token: string): UseChatReturn {
  const [state, setState] = useState<ChatUIState>(initialState);

  const sendMessage = async (text: string) => {
    // Implementation
  };

  return { state, setState, sendMessage, retry, resetConversation };
}
```

---

### useJWTToken

Retrieves JWT token from localStorage.

```typescript
export function useJWTToken(): string | null {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("auth_token");
    setToken(t);
  }, []);

  return token;
}
```

---

## API Client

### chat-client.ts

Encapsulates all chat API calls.

```typescript
export async function sendChatMessage(
  token: string,
  request: ChatRequest
): Promise<ChatResponse> {
  const userId = extractUserIdFromToken(token);  // Or from session

  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/api/${userId}/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify(request),
    }
  );

  if (!res.ok) {
    throw new ChatAPIError(res.status, await res.json());
  }

  return res.json();
}

export async function listConversations(
  token: string
): Promise<ConversationSummary[]> {
  // Implementation
}

export async function getConversation(
  token: string,
  conversationId: number
): Promise<ConversationDetail> {
  // Implementation
}

export async function deleteConversation(
  token: string,
  conversationId: number
): Promise<void> {
  // Implementation
}
```

---

## Type Definitions

### chat.ts

```typescript
// Message types
export interface Message {
  id: number;
  conversationId: number;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

// Conversation types
export interface Conversation {
  id: number;
  title?: string;
  createdAt: Date;
  messageCount: number;
}

export interface ConversationSummary {
  id: number;
  title?: string;
  created_at: string;
  message_count: number;
}

export interface ConversationDetail {
  id: number;
  title?: string;
  created_at: string;
  messages: MessageResponse[];
}

// API models
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

// UI state
export interface ChatUIState {
  conversationId: number | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  inputValue: string;
  lastUpdated: Date;
  messageCount: number;
}
```

---

## Design System Integration

### Tailwind Classes

**Message Bubbles**:
- User: `bg-cyan-500/20 text-right rounded-lg px-4 py-2`
- Assistant: `bg-teal-500/20 text-left rounded-lg px-4 py-2`

**Input Area**:
- `border-t border-cyan-500/30 p-4 bg-black/30`

**Buttons**:
- Primary: Existing Button component (design system)
- Secondary: Text button with hover effect

**Colors**:
- Primary: Teal (#0d9488)
- Accent: Cyan (#06b6d4)
- Background: Black with opacity (#000000 / 0.1-0.3)

---

## Performance Optimizations

### Potential Optimizations (Phase 2+)

1. **Message Virtualization**: For conversations with 100+ messages
2. **Lazy Loading**: Load older messages on scroll up
3. **Image Caching**: Cache assistant responses with React.memo
4. **Debouncing**: Debounce message input for typing indicators

### MVP (This Phase)

- No optimization needed for typical usage
- Expected: <100 messages per conversation
- Scrollable list sufficient for MVP