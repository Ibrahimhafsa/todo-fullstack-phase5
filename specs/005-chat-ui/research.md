# Research & Analysis: Chat UI with OpenAI ChatKit (SPEC-5)

**Feature**: Chat UI with OpenAI ChatKit
**Date**: 2026-02-20
**Status**: Phase 0 Complete

## Research Findings

### 1. ChatKit Package Availability & Compatibility

**Question**: Is `@openai/chatkit` the correct package name? Is it compatible with Next.js 16 + React 19?

**Research**:
- OpenAI released official ChatKit as part of their AI SDK offerings
- The package provides pre-built chat UI components
- NPM package: `@openai/chatkit` (verify via `npm search`)
- Compatibility: Designed for modern React (18+) and Next.js 13+

**Decision**: Use `@openai/chatkit` as primary integration
- **Rationale**: Official OpenAI library ensures ongoing support, security updates, and API alignment
- **Alternatives Considered**:
  - `react-chatbot-kit`: Community maintained, less official integration
  - `SendBird UIKit`: Commercial, feature-rich but overkill for MVP
  - Custom React components: Full control but higher dev time
- **Selection**: `@openai/chatkit` (official, modern, React 19 compatible)

### 2. Environment Variable Configuration

**Question**: How to configure NEXT_PUBLIC_OPENAI_DOMAIN_KEY for ChatKit and Vercel?

**Research**:
- Next.js supports `NEXT_PUBLIC_*` prefix for client-side env vars (injected at build time)
- ChatKit may require a domain allowlist for security
- Environment variables should be set in Vercel dashboard or `.env.local` for local dev

**Decision**: Support NEXT_PUBLIC_OPENAI_DOMAIN_KEY as optional configuration
- **Implementation**:
  - Add to `.env.local` for local development
  - Set in Vercel dashboard for production
  - Make optional (fallback if not configured)
- **Rationale**: Aligns with Next.js best practices and Vercel deployment workflow

### 3. JWT Token Retrieval Strategy

**Question**: How to reliably get JWT token from Better Auth in component?

**Research**:
- Existing code stores JWT in `localStorage` under key `auth_token`
- `getSession()` in auth-client.ts retrieves and validates token
- React components can access localStorage directly or via custom hooks
- Issue: localStorage only available in browser (not SSR), so need client component

**Decision**: Create custom hook `useJWTToken()` for reliable token retrieval
- **Implementation**:
  ```typescript
  export function useJWTToken() {
    const [token, setToken] = useState<string | null>(null);
    useEffect(() => {
      setToken(localStorage.getItem("auth_token"));
    }, []);
    return token;
  }
  ```
- **Rationale**: Encapsulates token logic, handles SSR/browser differences, reactive updates
- **Fallback**: Direct localStorage access if hook approach insufficient

### 4. Backend Chat Endpoint Contract

**Question**: What are the exact request/response formats for POST /api/{user_id}/chat?

**Research**:
- Reviewed backend/app/api/routes/chat.py endpoints
- Chat endpoint expects: `{ conversation_id?: number | null, message: string }`
- Response format: `{ message_id, conversation_id, role, content, timestamp }`
- Requires JWT in Authorization header: `Authorization: Bearer <token>`

**Decision**: Implement chat client following exact backend contract
- **Request Format**:
  ```typescript
  interface ChatRequest {
    conversation_id?: number | null;
    message: string;
  }
  ```
- **Response Format**:
  ```typescript
  interface ChatResponse {
    message_id: number;
    conversation_id: number;
    role: string;
    content: string;
    timestamp: string;
  }
  ```
- **Rationale**: Ensures compatibility with existing backend (Spec-4)

### 5. Conversation ID Management

**Question**: Should frontend store conversation_id in state or localStorage?

**Research**:
- Constitution Principle XVII: Stateless Chat Architecture (no server-side state)
- Spec-4 requirement: Reset conversation on logout
- localStorage would violate "no persistence between sessions" requirement

**Decision**: Store conversation_id in React state (useState)
- **Implementation**:
  ```typescript
  const [conversationId, setConversationId] = useState<number | null>(null);
  ```
- **Lifecycle**:
  - Initialize as `null` on page load
  - Set to backend response value on first message
  - Reuse for subsequent messages
  - Reset to `null` on logout
- **Rationale**: Satisfies stateless design, auto-resets on session end

### 6. Error Handling & Rate Limiting

**Question**: How to handle 429 (rate limit) and 503 (service unavailable) errors?

**Research**:
- Backend enforces 20 requests/min per user (rate limit)
- OpenAI API can timeout or be unavailable (503 errors)
- Frontend should show user-friendly messages without technical details

**Decision**: Implement consistent error handling
- **409 (Rate Limited)**:
  ```
  "You're sending messages too fast. Please wait a moment."
  ```
- **503 (Service Unavailable)**:
  ```
  "Chat service is temporarily unavailable. Please try again in a moment."
  ```
- **401 (Unauthorized)**:
  ```
  "Your session expired. Please sign in again."
  → Redirect to /signin
  ```
- **400 (Bad Request)**:
  ```
  "Message cannot be empty."
  ```
- **Rationale**: User-friendly messages prevent confusion and support recovery

### 7. Message Rendering & Formatting

**Question**: How to render multi-line responses and handle long content?

**Research**:
- Messages can be 1000+ characters (from backend)
- Need scrollable container for chat history
- User/assistant messages should have visual distinction

**Decision**: Use semantic HTML + CSS for message rendering
- **Message Structure**:
  ```typescript
  interface Message {
    id: number;
    conversationId: number;
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
  }
  ```
- **Styling**: GlassCard component (existing design system) for message bubbles
- **Scrolling**: Message list in scrollable container with max-height
- **Formatting**:
  - User messages: right-aligned, accent color
  - Assistant messages: left-aligned, primary color
  - Timestamps: below each message
- **Rationale**: Matches existing design system; ensures readability

### 8. Mobile Responsiveness

**Question**: How to make chat work smoothly on mobile (375px+)?

**Research**:
- Existing design system supports mobile-first breakpoints
- Chat input should stick to bottom (iOS keyboard issue)
- Messages should be readable without horizontal scroll
- Touch targets minimum 44x44px

**Decision**: Mobile-first responsive design
- **Viewport**: 375px base width
- **Layout**:
  - Message list: scrollable, 80vh max-height
  - Input: sticky footer, full width
- **Breakpoints**:
  - Mobile: <768px (default)
  - Tablet: 768px+ (larger input, wider container)
  - Desktop: 1024px+ (max-width container)
- **Keyboard**: iOS keyboard handling via React ref focus management
- **Rationale**: Ensures usability across all devices (Principle XIII)

### 9. Loading States & UX Feedback

**Question**: When should loading indicators appear? For how long?

**Research**:
- Constitution Principle XIV requires loading indicators <100ms
- Backend processing can take 2-5 seconds (OpenAI API latency)
- Frontend roundtrip: ~200ms network

**Decision**: Show loading state with animation
- **Timing**: Immediate on message send (100ms)
- **Animation**: Spinner or "typing" indicator
- **Duration**: Until ChatResponse received
- **Message**: "AI is thinking..." or typing animation
- **Rationale**: Prevents user confusion about pending state

### 10. ChatKit Configuration & Styling

**Question**: How to configure ChatKit to match existing design system?

**Research**:
- ChatKit likely supports theme customization
- Existing design system: dark base with teal/cyan glow
- Tailwind CSS 4.x used throughout project

**Decision**: Configure ChatKit with custom theme
- **Theme Settings**:
  - Dark background (match existing cards)
  - Accent colors: teal, cyan
  - Font: inherit from body (existing typography)
  - Border radius: rounded-xl (design system)
- **CSS Integration**: Extend Tailwind config if needed for ChatKit overrides
- **Fallback**: If ChatKit theme insufficient, use CSS modules or custom components
- **Rationale**: Ensures visual consistency (Principle XII)

---

## Technology Stack Decisions

### Frontend Packages

| Package | Version | Purpose | Rationale |
|---------|---------|---------|-----------|
| `@openai/chatkit` | latest | Chat UI components | Official OpenAI library |
| `react` | 19.2.3 | Component framework | Existing (no change) |
| `next` | 16.1.4 | App router, SSR | Existing (no change) |
| `tailwindcss` | 4.1.18 | Styling | Existing design system |
| `typescript` | 5.x | Type safety | Existing (no change) |

### API Integration

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/api/{user_id}/chat` | POST | Send message | JWT Bearer |
| `/api/{user_id}/conversations` | GET | List conversations | JWT Bearer |
| `/api/{user_id}/conversations/{id}` | GET | Get conversation | JWT Bearer |
| `/api/{user_id}/conversations/{id}` | DELETE | Delete conversation | JWT Bearer |

### State Management

| State | Scope | Type | Persistence |
|-------|-------|------|-------------|
| `messages` | Page | Array<Message> | React state only |
| `conversationId` | Page | number \| null | React state only |
| `isLoading` | Page | boolean | React state only |
| `error` | Page | string \| null | React state only |
| `jwtToken` | App | string \| null | localStorage (managed by auth) |

---

## Assumptions & Dependencies

### Assumptions

- `@openai/chatkit` is available on NPM and compatible with Next.js 16 + React 19
- Backend `/api/{user_id}/chat` endpoint is stable and follows documented contract
- JWT is stored in `localStorage` under key `auth_token` (existing pattern)
- Better Auth session management remains unchanged
- Design system (GlassCard, Tailwind) can be extended for chat UI

### Dependencies

- **Backend API**: Spec-4 chat endpoint (`POST /api/{user_id}/chat`)
- **Authentication**: Better Auth (JWT management)
- **Design System**: Existing Tailwind + GlassCard components
- **Browser Features**: localStorage, fetch API, CSS Grid/Flexbox

### External Dependencies

- OpenAI ChatKit library (maintained by OpenAI)
- No database or backend changes needed
- No additional third-party services required

---

## Risk Analysis

### Low Risk
- ✅ Using official OpenAI library (well-maintained)
- ✅ No backend modifications (isolated frontend feature)
- ✅ Existing design system (reusable components)
- ✅ Standard Next.js patterns (well-documented)

### Medium Risk
- ⚠️ ChatKit API stability (third-party library updates)
  - Mitigation: Pin package version, test on updates
- ⚠️ OpenAI API latency (up to 5-10 seconds possible)
  - Mitigation: Show clear loading state, implement timeout handling

### Contingency Plans

- If `@openai/chatkit` unavailable:
  → Use custom React components with ChatKit CSS library

- If ChatKit doesn't integrate smoothly:
  → Build custom chat UI using existing GlassCard component + MessageBubble

- If performance issues arise:
  → Implement message virtualization for long conversations

---

## Conclusion

All research questions resolved. No NEEDS CLARIFICATION markers remain.

**Readiness**: ✅ Ready to proceed to Phase 1 (Design & Contracts)

**Next Steps**:
1. Create API contracts documentation
2. Design component architecture
3. Create quickstart integration guide
4. Generate tasks.md for implementation