# Implementation Plan: Chat UI with OpenAI ChatKit

**Branch**: `005-chat-ui` | **Date**: 2026-02-20 | **Spec**: [spec.md](spec.md)
**Input**: Build a production-ready chat UI frontend using OpenAI ChatKit, integrating with existing Spec-4 backend agent.

**Note**: This template is filled by `/sp.plan` command for frontend-only implementation of chat UI.

## Summary

Build a modern, responsive chat UI frontend using OpenAI ChatKit that enables users to send messages to the Spec-4 AI backend agent. The frontend will manage conversation state, display messages with proper loading/error states, and maintain conversation context via `conversation_id` returned by backend. No backend modifications allowed; integration is frontend-only via existing `POST /api/{user_id}/chat` endpoint with JWT authentication.

**Key Technical Approach**:
- Install `@openai/chatkit` and configure with environment variable
- Create isolated `/chat` page using Next.js 16 App Router
- Implement React state management for messages, loading, and error states
- Integrate with existing Better Auth for JWT token retrieval
- Handle conversation lifecycle (create, maintain context, reset on logout)
- Apply existing design system (teal/cyan/black glow theme) for consistency

## Technical Context

**Language/Version**: TypeScript 5.x (Next.js 16+, React 19)
**Primary Dependencies**:
- `@openai/chatkit` - Chat UI component library
- `better-auth` (existing) - JWT management
- `tailwindcss` 4.x - Styling (existing design system)
- Standard `fetch` API (no axios needed)

**Storage**: None on frontend; Conversation state stored in React state only (no localStorage persistence as per Spec-4 stateless design)

**Testing**: Jest/React Testing Library (component testing); no E2E needed for MVP

**Target Platform**: Web browser (Chrome, Safari, Firefox, Edge 2022+); Mobile-responsive (375px+)

**Project Type**: Web frontend (Next.js SPA with server-side rendering)

**Performance Goals**:
- Message response display: <5 seconds (including backend processing)
- Loading indicator visible: <200ms
- Page navigation: <100ms
- Mobile-first optimization

**Constraints**:
- <100KB additional bundle size (ChatKit footprint)
- No backend modifications allowed
- JWT must be retrieved from existing auth system
- `conversation_id` management must follow backend contract

**Scale/Scope**: Single chat page; up to 100 messages per conversation; 1000+ concurrent users via backend scalability

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Applicable Principles** (from Constitution v2.0.0):

✅ **Principle I (JWT-Only Authentication)**: Chat will use existing JWT in Authorization header
✅ **Principle II (Shared Secret Sync)**: No changes to auth; relies on existing infrastructure
✅ **Principle XV (Frontend-Backend Integration)**: Will include JWT in every chat request
✅ **Principle XVI (Phase-2 Read-Only)**: No task CRUD code modifications; new feature only
✅ **Principle XVII (Stateless Chat Architecture)**: Frontend will not store backend session state
✅ **Principle XVIII (JWT Security for Chat)**: Every chat endpoint call requires valid JWT
✅ **Principle XXII (Chat Frontend Isolation)**: Chat at `/chat` route, separate from dashboard at `/`
✅ **Principle XI (Frontend Workspace Isolation)**: All work in `/frontend` directory only
✅ **Principle XII (Design System Compliance)**: Will use existing teal/cyan/black glow theme
✅ **Principle XIII (Responsive Layout)**: Mobile-first breakpoints; works 320px to 2560px
✅ **Principle XIV (UX State Management)**: Loading, empty, error states required

**Gate Evaluation**: ✅ **PASS** — No constitutional violations detected. All constraints respected:
- No backend modifications (frontend-only)
- No database changes
- JWT handled via existing infrastructure
- Chat isolated from dashboard
- Design system compliance ensured

## Project Structure

### Documentation (this feature)

```text
specs/005-chat-ui/
├── spec.md              # Feature specification (COMPLETE)
├── plan.md              # This file (implementation plan)
├── research.md          # Phase 0 output (dependency research)
├── data-model.md        # Phase 1 output (data model design)
├── quickstart.md        # Phase 1 output (integration guide)
├── contracts/           # Phase 1 output (API contracts)
│   └── chat-api.md
├── checklists/
│   └── requirements.md  # Quality validation (COMPLETE)
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (Frontend - Next.js)

```text
frontend/
├── app/
│   ├── (protected)/
│   │   ├── chat/                    # NEW: Chat feature route
│   │   │   ├── page.tsx             # NEW: Chat page component
│   │   │   └── layout.tsx           # NEW: Chat layout (optional)
│   │   └── dashboard/               # EXISTING: Task dashboard (unchanged)
│   ├── (auth)/                      # EXISTING: Auth pages (unchanged)
│   │   ├── signin/
│   │   └── signup/
│   └── layout.tsx                   # EXISTING: Root layout (unchanged)
│
├── components/
│   ├── chat/                        # NEW: Chat-specific components
│   │   ├── ChatContainer.tsx        # Main chat wrapper
│   │   ├── MessageList.tsx          # Message display container
│   │   ├── MessageBubble.tsx        # Individual message component
│   │   ├── ChatInput.tsx            # Message input component
│   │   ├── LoadingIndicator.tsx     # Loading state
│   │   ├── ErrorMessage.tsx         # Error display
│   │   └── ConversationList.tsx     # Conversation history (optional)
│   ├── ui/                          # EXISTING: Design system components
│   │   ├── Button.tsx               # EXISTING
│   │   ├── GlassCard.tsx            # EXISTING (reuse for messages)
│   │   └── ... other UI components
│   ├── providers/
│   │   └── AuthProvider.tsx         # EXISTING (no changes)
│   └── tasks/                       # EXISTING: Task components (unchanged)
│
├── lib/
│   ├── api.ts                       # EXISTING: API client
│   ├── auth-client.ts               # EXISTING: Auth logic (no changes)
│   ├── chat-client.ts               # NEW: Chat API client (wraps POST /api/{user_id}/chat)
│   ├── hooks/
│   │   ├── useTasks.ts              # EXISTING
│   │   ├── useChat.ts               # NEW: Chat state management hook
│   │   ├── useChatMessages.ts       # NEW: Message history hook
│   │   └── useConversation.ts       # NEW: Conversation context hook
│   ├── types/
│   │   ├── task.ts                  # EXISTING
│   │   └── chat.ts                  # NEW: Chat types (Message, Conversation)
│   └── utils/
│       └── chatHelpers.ts           # NEW: Utility functions for chat (format dates, etc.)
│
├── styles/
│   └── globals.css                  # EXISTING: Tailwind + custom CSS (no changes)
│
├── .env.local                       # EXISTING: Environment config
│   └── (will add NEXT_PUBLIC_OPENAI_DOMAIN_KEY)
│
└── package.json                     # UPDATE: Add @openai/chatkit dependency
```

**Structure Decision**: Web application layout (Option 2) with clear isolation:
- Chat feature fully contained in `/app/(protected)/chat/` route
- Shared UI components in `/components/ui/` (design system compliance)
- Chat-specific components in `/components/chat/` (isolation)
- Existing dashboard at `/app/(protected)/dashboard/` remains unchanged
- No modifications to auth or task components
- Clear separation maintains Constitution Principle XXII

## Complexity Tracking

**No constitutional violations detected** — All principles satisfied by design.
- ✅ Frontend-only implementation (no backend changes)
- ✅ Chat isolated from dashboard (separate route)
- ✅ JWT handled via existing infrastructure
- ✅ Design system compliance verified
- ✅ Responsive design enforced

---

## Phase 0: Research & Dependency Analysis

### Research Tasks

1. **ChatKit Integration Research** (REQUIRED)
   - Question: Is `@openai/chatkit` the correct package name?
   - Resources: NPM docs, OpenAI documentation
   - Decision Path: Verify package availability, installation, version compatibility
   - Fallback: Use alternative chat UI library if ChatKit not available (e.g., `react-chatbot-kit`, custom components)

2. **Environment Variable Configuration** (REQUIRED)
   - Question: How to configure NEXT_PUBLIC_OPENAI_DOMAIN_KEY?
   - Resources: Next.js env vars, ChatKit configuration
   - Decision Path: Document env var setup for Vercel deployment
   - Fallback: Make this optional if not required by ChatKit

3. **JWT Token Retrieval** (REQUIRED)
   - Question: How to reliably get JWT token from Better Auth in component?
   - Resources: Existing auth-client.ts pattern
   - Decision Path: Reuse getSession() approach, extract token from localStorage
   - Fallback: Create custom hook for token retrieval

4. **API Response Parsing** (REQUIRED)
   - Question: What exact fields does POST /api/{user_id}/chat return?
   - Resources: Backend chat.py routes (FR-001 to FR-010 responses)
   - Decision Path: Verify ChatResponse model structure
   - Expected: `{ message_id, conversation_id, role, content, timestamp }`
   - Fallback: Handle variations in response format gracefully

5. **Rate Limiting** (OPTIONAL)
   - Question: Should frontend implement client-side rate limiting UI?
   - Resources: Backend sets 20 req/min limit
   - Decision Path: Show "Rate limited" message on 429
   - Fallback: Just show generic error if not implemented

### Research Findings (Template - to be filled)

**Decision: ChatKit Package**
- Rationale: Official OpenAI library for chat UI
- Alternatives: Custom React components, react-chat-engine, SendBird
- Selection: `@openai/chatkit` (verify availability and compatibility)

**Decision: JWT Token Management**
- Rationale: Reuse existing getSession() pattern in auth-client.ts
- Implementation: Custom hook `useJWTToken()` that returns token from localStorage
- Fallback: Direct localStorage access if hook not sufficient

**Decision: Conversation ID Storage**
- Rationale: Store in React state (useState) per Spec-4 stateless design
- Implementation: Lift conversation state to top-level chat component
- Persistence: Reset on logout; no localStorage persistence

**Decision: Error Handling Strategy**
- Rationale: Show user-friendly messages; log technical details to console
- Implementation: Try/catch blocks with custom error messages
- Fallback: Show generic "Chat service unavailable" on 503

---

## Phase 1: Design & Contracts

### Data Model

**Frontend State Model** (React State)

```typescript
// Chat.tsx state
const [messages, setMessages] = useState<Message[]>([]);
const [conversationId, setConversationId] = useState<number | null>(null);
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
const [inputValue, setInputValue] = useState("");

// Types
interface Message {
  id: number;
  conversationId: number;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface Conversation {
  id: number;
  title?: string;
  createdAt: Date;
  messageCount: number;
}

interface ChatResponse {
  message_id: number;
  conversation_id: number;
  role: string;
  content: string;
  timestamp: string;
}
```

### API Contracts

**Backend Chat Endpoint** (existing, from Spec-4)

```
POST /api/{user_id}/chat
Request:
  {
    "conversation_id": number | null,
    "message": string
  }

Response (200 OK):
  {
    "message_id": number,
    "conversation_id": number,
    "role": "assistant",
    "content": string,
    "timestamp": ISO8601
  }

Error Responses:
  401: User ID mismatch / invalid JWT
  400: Empty message
  404: Conversation not found
  429: Rate limit exceeded
  503: OpenAI service unavailable
```

**Frontend ChatKit Configuration**

```typescript
// Pseudo-config for ChatKit integration
const chatKitConfig = {
  apiKey: process.env.NEXT_PUBLIC_OPENAI_DOMAIN_KEY,
  mode: "embedded", // Chat UI embedded in page
  theme: "dark",    // Matches design system
  messages: messages,
  onSendMessage: async (text: string) => {
    // Call POST /api/{user_id}/chat
    // Update state with response
  },
};
```

### Component Architecture

**Message Flow**:
```
ChatPage.tsx (Route)
├── ChatContainer.tsx (Wrapper)
├── MessageList.tsx
│   └── MessageBubble.tsx (x N messages)
├── ChatInput.tsx
│   └── Button (Send)
├── LoadingIndicator.tsx (conditional)
└── ErrorMessage.tsx (conditional)
```

**State Management**:
- `useChat()` hook: Manages messages, conversationId, loading, error
- `useJWTToken()` hook: Retrieves JWT from localStorage / session
- React Context (optional): Share chat state across components if needed

### Quickstart Integration

**Steps to Integrate Chat**:

1. Install ChatKit:
   ```bash
   npm install @openai/chatkit
   ```

2. Add environment variable:
   ```env
   NEXT_PUBLIC_OPENAI_DOMAIN_KEY=your-key-here
   ```

3. Create chat page:
   ```
   frontend/app/(protected)/chat/page.tsx
   ```

4. Implement components:
   - ChatContainer.tsx (main component)
   - MessageBubble.tsx (message display)
   - ChatInput.tsx (input box)

5. Create API client:
   ```
   frontend/lib/chat-client.ts
   ```

6. Create custom hooks:
   - useChat() - state management
   - useJWTToken() - token retrieval

7. Update package.json and install dependencies

8. Test locally: `npm run dev` → navigate to `/chat`

### Mobile Responsiveness

**Responsive Design Strategy**:
- Mobile-first approach (375px base)
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Chat input sticky to bottom on mobile
- Message list scrollable with max-height
- Design system: Use existing Tailwind setup + GlassCard components

---

## Integration Points

### With Existing Systems

**Authentication (Spec-1)**:
- Use existing `getSession()` to retrieve JWT
- No auth modifications needed
- JWT automatically included in Authorization header

**Dashboard (Spec-3)**:
- Chat at `/chat` route (separate from `/dashboard`)
- No shared state with task components
- Navigation: Add "Chat" link in Navbar if needed

**Backend (Spec-4)**:
- Integration: `POST /api/{user_id}/chat`
- Contract: ChatRequest/ChatResponse models (existing)
- No backend modifications required

---

## Deployment & Configuration

### Vercel Setup

**Environment Variables**:
```
NEXT_PUBLIC_OPENAI_DOMAIN_KEY=production-key-here
NEXT_PUBLIC_API_URL=https://api.production.com
```

**Build Configuration**:
- No custom build steps needed
- ChatKit CSS bundled automatically
- Next.js 16 app router handles routing

### Local Development

**Setup**:
1. Install dependencies: `npm install`
2. Add `.env.local` with NEXT_PUBLIC_OPENAI_DOMAIN_KEY
3. Start backend: `cd backend && python -m uvicorn app.main:app --reload`
4. Start frontend: `npm run dev`
5. Navigate to `http://localhost:3000/chat`

**Testing**:
- Send test message → verify response displays
- Check browser console for errors
- Verify JWT included in requests (DevTools → Network)
- Test mobile view (DevTools → Device Toolbar)

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
