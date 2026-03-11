# Tasks: Chat UI with OpenAI ChatKit

**Feature**: SPEC-5 Chat UI with OpenAI ChatKit
**Branch**: `005-chat-ui`
**Date**: 2026-02-20
**Input**: Design documents from `/specs/005-chat-ui/`

**Prerequisites**:
- ✅ plan.md (Architecture & Technical Context)
- ✅ spec.md (4 User Stories with priorities)
- ✅ research.md (Technology decisions)
- ✅ data-model.md (Component & data design)
- ✅ contracts/chat-api.md (API specifications)
- ✅ quickstart.md (Implementation guide)

**Tests**: None explicitly requested in spec (user acceptance scenarios used instead)

**Organization**: Tasks grouped by user story (P1→P2) to enable independent development and testing.

---

## Format Guide

- **`- [ ] [ID]`**: Checkbox task identifier
- **`[P]`**: Parallelizable (different files, no blocking dependencies)
- **`[US#]`**: User Story number (US1, US2, US3, US4)
- **File paths**: Absolute within `/frontend/` directory

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and ChatKit integration
**Duration**: ~30 minutes
**Blocker**: All user stories depend on Phase 1 completion

### Setup Tasks

- [ ] T001 Install ChatKit dependency: `npm install @openai/chatkit` in `/frontend/` directory
- [ ] T002 Add environment variable `NEXT_PUBLIC_OPENAI_DOMAIN_KEY` to `/frontend/.env.local` with placeholder value
- [ ] T003 Create type definitions file: `/frontend/lib/types/chat.ts` with Message, Conversation, ChatRequest, ChatResponse, ChatUIState interfaces
- [ ] T004 [P] Create API client file: `/frontend/lib/chat-client.ts` with sendChatMessage, listConversations, getConversation, deleteConversation functions
- [ ] T005 [P] Create JWT token hook: `/frontend/lib/hooks/useJWTToken.ts` that retrieves token from localStorage with useEffect
- [ ] T006 [P] Create chat state hook: `/frontend/lib/hooks/useChat.ts` with reducer pattern managing messages, conversationId, loading, error states
- [ ] T007 Create chat directory structure: `/frontend/components/chat/` (create directory only, components added in Phase 2)
- [ ] T008 Verify Next.js 16 App Router compatibility: Test that `frontend/app/(protected)/` routing works correctly

**Checkpoint**: ✅ All infrastructure in place. Ready to build UI components.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core UI components and routing that ALL user stories depend on
**Duration**: ~45 minutes
**Blocker**: All user stories blocked until Phase 2 complete

### Foundational UI Components

- [ ] T009 Create chat page route: `/frontend/app/(protected)/chat/page.tsx` with auth guard, JWT token retrieval, user ID extraction
- [ ] T010 [P] Create MessageBubble component: `/frontend/components/chat/MessageBubble.tsx` displaying message content, role-based styling (user right-aligned cyan, assistant left-aligned teal), timestamp
- [ ] T011 [P] Create ChatInput component: `/frontend/components/chat/ChatInput.tsx` with textarea, send button, Enter-to-send, Shift+Enter for newline, input validation
- [ ] T012 [P] Create MessageList container: `/frontend/components/chat/MessageList.tsx` displaying array of MessageBubble components, scrollable container, empty state
- [ ] T013 [P] Create LoadingIndicator component: `/frontend/components/chat/LoadingIndicator.tsx` with spinner animation, "AI is thinking..." text
- [ ] T014 [P] Create ErrorMessage component: `/frontend/components/chat/ErrorMessage.tsx` displaying error text, retry button, dismiss button
- [ ] T015 Create ChatContainer wrapper: `/frontend/components/chat/ChatContainer.tsx` orchestrating MessageList, ChatInput, LoadingIndicator, ErrorMessage with state management

**Checkpoint**: ✅ All UI components built and importable. Ready for feature implementation.

---

## Phase 3: User Story 1 - Send and Receive Messages (Priority: P1) 🎯 MVP

**Goal**: Users can send messages to AI and receive responses; messages display in chat UI with conversation history

**Independent Test**:
1. Navigate to `/chat` (logged in)
2. Type "Hello" and click Send
3. Message appears in chat as user message
4. Wait for response
5. Assistant message appears below
6. Both messages display with timestamps
7. Navigation back and forth doesn't lose history (in current session)

**User Story Requirements**:
- FR-001: Send message button and input field
- FR-002: Display user/assistant messages with distinction
- FR-003: Connect to `POST /api/{user_id}/chat` with JWT
- FR-004: Extract user_id from authenticated session
- FR-005: Store and maintain conversation_id
- FR-006: Include conversation_id in subsequent requests
- FR-007: Display loading indicator while waiting
- FR-008: Display response in human-readable format (no raw JSON)
- FR-009: Support multi-line responses with scrolling
- FR-011: Validate non-empty messages

### US1 Implementation Tasks

- [ ] T016 [US1] Implement sendMessage logic in useChat hook: call sendChatMessage API, handle ChatResponse, update state with both user and assistant messages
- [ ] T017 [US1] Implement conversation_id lifecycle in useChat: initialize as null, set on first response, reuse for subsequent messages, track current conversation
- [ ] T018 [US1] Wire ChatContainer handleSendMessage: accept text input, validate non-empty, call useChat.sendMessage, clear input field, update UI state
- [ ] T019 [US1] Add JWT token parameter to chat API calls: include `Authorization: Bearer {token}` header in sendChatMessage function
- [ ] T020 [US1] Add user ID extraction from JWT: implement extractUserIdFromToken in useJWTToken hook, decode JWT payload, extract 'sub' or 'id' claim
- [ ] T021 [US1] Pass token and userId to ChatContainer: useJWTToken hook in chat page, pass to ChatContainer props
- [ ] T022 [US1] Verify message display: user messages right-aligned cyan, assistant messages left-aligned teal, both with content and timestamp
- [ ] T023 [US1] Test first message flow: send message with null conversation_id, verify backend creates conversation, verify response includes conversation_id, verify UI shows response
- [ ] T024 [US1] Test subsequent messages: store conversation_id from first message, send second message with that conversation_id, verify backend acknowledges, verify both messages in history

**Checkpoint**: ✅ Core chat functionality working. Users can send/receive messages with conversation_id tracking.

---

## Phase 4: User Story 2 - Maintain Conversation Context (Priority: P1)

**Goal**: Chat maintains conversation_id across multiple exchanges; conversation resets on logout

**Independent Test**:
1. Send message 1: "Create a task"
2. Receive response with conversation_id=42
3. Send message 2: "Add another"
4. Verify message 2 request includes conversation_id=42
5. Receive response that references same conversation_id=42
6. Logout and login again
7. Navigate to `/chat` (new page load)
8. Send new message (should have null conversation_id)
9. Verify new conversation_id returned (different from 42)

**User Story Requirements** (same as US1 re: conversation_id):
- FR-005: Store and maintain conversation_id in React state
- FR-006: Include conversation_id in subsequent requests
- FR-012: Reset conversation state when user logs out
- US1 acceptance scenarios 1-3 (context maintained across exchanges, reset on logout)

### US2 Implementation Tasks

- [ ] T025 [US2] Verify conversation_id state persistence in useChat: useState persists conversation_id across renders, survives component re-renders
- [ ] T026 [US2] Implement conversation reset on logout: listen for logout event or auth state change, call reset() in useChat, set conversationId back to null
- [ ] T027 [US2] Test multi-turn dialogue: Send 3 messages sequentially, verify each request includes previous conversation_id, verify all responses reference same conversation
- [ ] T028 [US2] Test conversation_id in API requests: inspect browser DevTools Network tab, verify POST body includes conversation_id field (first message: null, subsequent: number)
- [ ] T029 [US2] Test logout reset: Send messages to establish conversation_id, logout (via navbar or auth mechanism), login again, verify new conversation_id on next message
- [ ] T030 [US2] Test page reload: Send messages, establish conversation_id, reload page (F5), verify conversation_id lost (localStorage not used per spec), verify new conversation_id on next message

**Checkpoint**: ✅ Conversation context fully functional. Multi-turn dialogue and logout reset working.

---

## Phase 5: User Story 3 - Error Handling and Resilience (Priority: P2)

**Goal**: Users see friendly error messages on failures; retry mechanism available for recovery

**Independent Test**:
1. Test backend error: Disconnect backend service, send message, verify error message displays (not technical error)
2. Test retry: Click retry button, backend comes back online, message resubmits, response displays
3. Test rate limit: Send 25 messages in 1 minute, verify 429 error message: "You're sending messages too fast..."
4. Test empty message: Try to send empty string or whitespace, verify error: "Message cannot be empty"
5. Test session timeout: Let JWT expire, send message, verify redirect to signin

**User Story Requirements**:
- FR-010: Display error messages with retry option
- FR-011: Validate non-empty messages
- Error handling for 400, 401, 404, 429, 503 status codes
- User-friendly error messages (no technical details)

### US3 Implementation Tasks

- [ ] T031 [US3] Implement error state in useChat: add error field to state, set on API failure, clear on new send attempt
- [ ] T032 [US3] Map API status codes to user-friendly messages: 429 → "Sending too fast...", 503 → "Service unavailable...", 401 → "Session expired...", 400 → "Invalid message"
- [ ] T033 [US3] Implement retry mechanism: store failed message text, add retry() function in useChat, re-send when user clicks retry
- [ ] T034 [US3] Handle ChatAPIError class: throw error with status and data in chat-client.ts, catch in useChat with proper error mapping
- [ ] T035 [US3] Add input validation: check message.trim().length > 0 before API call, show validation error if empty
- [ ] T036 [US3] Display error in UI: render ErrorMessage component when error state set, include retry button with onClick handler
- [ ] T037 [US3] Test 429 rate limit error: Send rapid messages, catch 429 response, verify user-friendly message in UI
- [ ] T038 [US3] Test 503 service unavailable: Mock backend timeout or 503, send message, verify error message and retry button appear
- [ ] T039 [US3] Test 400 validation error: Test empty message handling, verify validation error shows before API call
- [ ] T040 [US3] Test 401 unauthorized: Manually expire JWT in localStorage, send message, verify redirect to signin

**Checkpoint**: ✅ Robust error handling with recovery options.

---

## Phase 6: User Story 4 - Mobile-Responsive Chat (Priority: P2)

**Goal**: Chat works well on mobile devices (375px+) with readable text, accessible inputs, proper scrolling

**Independent Test**:
1. Open DevTools, select iPhone 12 (390px)
2. Navigate to `/chat`
3. Send message, receive response
4. Verify no horizontal scrolling
5. Verify text readable at mobile size
6. Verify send button clickable (44px+ touch target)
7. Focus on input, verify keyboard appears
8. Type and send message successfully
9. Verify messages stack vertically
10. Test on tablet (768px) and desktop (1920px)

**User Story Requirements**:
- FR-013: Responsive on desktop (1024px+) and mobile (375px+) viewports
- Constraint: Mobile-first breakpoints (sm, md, lg, xl from Tailwind)
- Design system: GlassCard, existing Tailwind theme

### US4 Implementation Tasks

- [ ] T041 [US4] Add Tailwind responsive classes to ChatContainer: flex-col for vertical stack, responsive padding/gaps, max-width container
- [ ] T042 [US4] Make MessageList scrollable on mobile: set max-height, overflow-y-auto, sticky footer for input area (bottom: 0)
- [ ] T043 [US4] Style MessageBubble for mobile: add line-breaks to long text (break-words, whitespace-pre-wrap), responsive padding
- [ ] T044 [US4] Make ChatInput sticky to bottom: position sticky/relative, width-full, responsive height and font size
- [ ] T045 [US4] Ensure touch targets 44px+: button height min 44px (py-2 = 20px, needs container padding), textarea height responsive
- [ ] T046 [US4] Test mobile viewport 375px: DevTools device mode, send message, verify full UI visible no horizontal scroll
- [ ] T047 [US4] Test tablet viewport 768px: DevTools tablet, verify layout adapts, message bubbles have appropriate width
- [ ] T048 [US4] Test desktop viewport 1920px: verify container has max-width, centered, readable message widths
- [ ] T049 [US4] Verify keyboard handling: mobile tap input field, native keyboard appears, typing and sending works
- [ ] T050 [US4] Test long response text: send message that triggers long assistant response (>1000 chars), verify text wraps, scrollable message area

**Checkpoint**: ✅ Chat fully responsive across all device sizes.

---

## Phase 7: Integration & Deployment (Production Readiness)

**Purpose**: Configure for production deployment, environment variables, domain allowlist

**Duration**: ~30 minutes

### Integration Tasks

- [ ] T051 Update `.env.local` for local development: set `NEXT_PUBLIC_OPENAI_DOMAIN_KEY=test-key` and `NEXT_PUBLIC_API_URL=http://localhost:8000`
- [ ] T052 [P] Add production configuration: document required Vercel environment variables in `.env.example` or README
- [ ] T053 [P] Verify no secrets in frontend code: grep for API keys, tokens, credentials in chat components (should be empty)
- [ ] T054 [P] Test with real JWT: use actual Better Auth token, verify chat API calls succeed with authentication
- [ ] T055 [P] Verify ChatKit CSS imports: ensure ChatKit styles load correctly, no CSS conflicts with Tailwind
- [ ] T056 Add navigation link to chat: update Navbar component to include `/chat` link (if nav exists)
- [ ] T057 Test dashboard unchanged: verify `/dashboard` still works, no shared state with chat page
- [ ] T058 Prepare Vercel configuration: document environment variables needed for production deployment

**Checkpoint**: ✅ Production-ready and deployable.

---

## Phase 8: Verification & Polish (Final Quality Gate)

**Purpose**: Cross-browser testing, edge cases, final UX polish

**Duration**: ~30 minutes

### Final Verification Tasks

- [ ] T059 [P] Test on Chrome, Safari, Firefox: verify chat works on each browser, no console errors
- [ ] T060 [P] Test with different network speeds: DevTools throttle to slow 3G, verify loading states appear, messages eventually arrive
- [ ] T061 [P] Test session expiration: let JWT expire during chat, send message, verify redirect to signin, verify no data loss
- [ ] T062 [P] Test rapid message sending: send 5 messages quickly, verify all queue properly, no lost messages
- [ ] T063 [P] Test very long responses: mock a 2000+ character response, verify scrolling works, readability maintained
- [ ] T064 [P] Test with special characters: send message with emoji, unicode, special characters, verify display correctly
- [ ] T065 Verify no console warnings: open DevTools console, use chat fully, verify no JavaScript warnings or errors
- [ ] T066 Verify design system compliance: compare colors, spacing, border radius against existing GlassCard components
- [ ] T067 Documentation: update README with `/chat` route description and setup instructions
- [ ] T068 Final acceptance test: walk through complete user flow (login → chat → multiple messages → logout → login → new chat) end-to-end

**Checkpoint**: ✅ Feature complete, tested, production-ready.

---

## Task Summary

| Phase | Tasks | Purpose | Duration |
|-------|-------|---------|----------|
| Phase 1: Setup | T001-T008 | Infrastructure & dependencies | ~30 min |
| Phase 2: Foundation | T009-T015 | UI components & routing | ~45 min |
| Phase 3: US1 | T016-T024 | Send/receive messages | ~60 min |
| Phase 4: US2 | T025-T030 | Conversation context | ~30 min |
| Phase 5: US3 | T031-T040 | Error handling | ~45 min |
| Phase 6: US4 | T041-T050 | Mobile responsiveness | ~45 min |
| Phase 7: Integration | T051-T058 | Production readiness | ~30 min |
| Phase 8: Verification | T059-T068 | Quality & polish | ~30 min |
| **TOTAL** | **68 tasks** | **Full feature** | **~5 hours** |

---

## Parallel Execution Strategy

### Setup Phase (T001-T008): Sequential
- T001: Install packages first
- T002: Configure env vars
- T003-T006: Types and API client can run in parallel [P]
- T007-T008: Verify setup

### Foundation Phase (T009-T015):
- T009: Create route (prerequisite for T010-T015)
- T010-T014: Components can run in parallel [P]
- T015: Wire components together (depends on T010-T014)

### Feature Phases (US1-US4):
- US1 (T016-T024): Build core chat
- US2 (T025-T030): Depends on US1 completion
- US3 (T031-T040): Error handling, can run parallel with US2
- US4 (T041-T050): Responsive, can run parallel with US3

### Integration & Verification (T051-T068):
- T051-T055: Configuration tasks, mostly parallel
- T056-T058: Integration tasks
- T059-T065: Verification tasks, can run parallel
- T066-T068: Final polish tasks

**Recommended Execution Order**:
1. Phase 1 (Setup) → Complete sequentially
2. Phase 2 (Foundation) → Complete sequentially
3. Phases 3-6 (Features) → Can interleave after Phase 2 (US1 → US2 sequential, US3 parallel, US4 parallel)
4. Phase 7 (Integration) → After all features complete
5. Phase 8 (Verification) → Final gate

---

## MVP Scope (Minimum Viable Product)

**Recommended first release: Phases 1-4 (US1 + US2)**

**MVP Deliverables**:
- ✅ Users can send messages and receive responses
- ✅ Conversation history displays in chat
- ✅ Conversation_id maintained across messages
- ✅ Works when logged in

**Not in MVP (Phase 2 release)**:
- Error handling polish (US3)
- Mobile responsiveness (US4)
- Production deployment (Phase 7-8)

**MVP Estimated Time**: ~2.5 hours (Phases 1-4 only)

---

## Dependencies Graph

```
Phase 1: Setup
    ↓
Phase 2: Foundation (UI Components & Route)
    ├→ Phase 3: US1 (Send/Receive)
    │   ├→ Phase 4: US2 (Context)
    │   │   ├→ Phase 5: US3 (Error Handling) [parallel with US2]
    │   │   └→ Phase 6: US4 (Mobile) [parallel with US3]
    │   └→ Phase 7: Integration [after all features]
    │       └→ Phase 8: Verification [final gate]
```

---

## Constraints & Guarantees

✅ **Frontend-only**: All 68 tasks are in `/frontend/` directory
✅ **No backend modifications**: Zero changes to backend code or database
✅ **No existing feature disruption**: Dashboard and auth untouched
✅ **Reversible**: Each task can be undone independently or in groups
✅ **Safe**: No destructive operations, all additive
✅ **Testable**: Each phase independently verifiable
✅ **Constitutional compliance**: All tasks respect Principles I, XI, XII, XIII, XIV, XVI, XVII, XVIII, XXII

---

## Implementation Checklist

- [ ] Phase 1 complete & verified
- [ ] Phase 2 complete & verified
- [ ] Phase 3 (US1) complete & accepted
- [ ] Phase 4 (US2) complete & accepted
- [ ] Phase 5 (US3) complete & accepted
- [ ] Phase 6 (US4) complete & accepted
- [ ] Phase 7 (Integration) complete
- [ ] Phase 8 (Verification) complete & approved
- [ ] All tests passing
- [ ] Ready for production deployment

---

## Quick Reference: Task IDs by Component

**Type Definitions**: T003
**API Client**: T004
**Hooks**: T005, T006
**Chat Page**: T009
**Components**: T010-T014
**ChatContainer**: T015
**Core Logic**: T016-T030
**Error Handling**: T031-T040
**Mobile**: T041-T050
**Production**: T051-T068