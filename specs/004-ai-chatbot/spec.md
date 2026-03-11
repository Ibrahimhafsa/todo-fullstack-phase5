# Feature Specification: AI Chatbot with MCP Tools & Agent Backend

**Feature Branch**: `004-ai-chatbot`
**Created**: 2026-02-18
**Status**: Draft
**Input**: Backend AI layer using OpenAI Agents SDK, MCP Server, stateless chat, and conversation persistence. Extends Phase-2 task endpoints via MCP tools.

## User Scenarios & Testing

### User Story 1 - Ask AI to Help Manage Tasks (Priority: P1)

As a user, I want to ask the AI chatbot to help me manage my tasks in natural language, so I can quickly accomplish task operations without manually clicking through the UI.

**Why this priority**: This is the core value proposition of the chatbot feature. Without this, there's no reason to add chat functionality. P1 ensures the feature has immediate user value.

**Independent Test**: Can be fully tested by: user sends message like "Create a task called 'Buy groceries'", AI processes it, creates the task via MCP tools, returns confirmation. Delivers: AI-augmented task management workflow.

**Acceptance Scenarios**:

1. **Given** user is authenticated and in the chat interface, **When** user sends message "Create a task called 'Buy groceries' with description 'Milk and bread'", **Then** AI agent calls `create_task` MCP tool, task is created in database, and AI responds with confirmation message including task ID
2. **Given** user is authenticated in chat, **When** user sends message "Show me all my tasks", **Then** AI agent calls `list_tasks` MCP tool, receives user's task list, and responds with formatted summary of tasks
3. **Given** chat conversation exists with task context, **When** user sends follow-up message "Mark the first one complete", **Then** AI agent identifies correct task from conversation context, calls `complete_task` MCP tool, and confirms completion

---

### User Story 2 - Maintain Chat Conversation History (Priority: P1)

As a user, I want the chatbot to remember my entire conversation history, so I can reference past commands and maintain context across multiple messages.

**Why this priority**: Conversation persistence is essential for multi-turn agent interactions. Without it, the agent loses context and can't follow up. P1 for feature viability.

**Independent Test**: Can be fully tested by: user sends 5 messages in one chat session, closes browser/page, returns to same conversation, verifies all 5 messages still visible with full context. Delivers: durable conversation state across sessions.

**Acceptance Scenarios**:

1. **Given** user starts a new conversation, **When** user sends 3 messages and agent responds, **Then** all messages and responses are stored in database under that conversation
2. **Given** conversation exists with 5 message pairs (user + assistant), **When** user retrieves conversation history, **Then** all messages display in chronological order with role (user/assistant) correctly identified
3. **Given** user has multiple conversations, **When** user switches between conversations, **Then** each conversation maintains independent message history with no cross-contamination

---

### User Story 3 - Use AI to Automate Common Task Operations (Priority: P2)

As a user, I want the AI to understand natural language commands like "delete old tasks" or "complete all urgent items", so I can perform bulk operations through conversation instead of manual clicks.

**Why this priority**: This enables power-user workflows but requires agent intelligence to parse context. P2 because core task CRUD is covered in P1; this adds convenience.

**Independent Test**: Can be fully tested by: user sends message "Complete my first 3 tasks", AI processes, calls `complete_task` 3 times with correct task IDs, confirms all 3. Delivers: conversational bulk operations.

**Acceptance Scenarios**:

1. **Given** user has 5 tasks with various states, **When** user sends "Complete all my tasks", **Then** AI agent calls `complete_task` for each incomplete task and confirms total count
2. **Given** user references task by name or context, **When** AI agent needs to identify specific task, **Then** agent queries `list_tasks`, finds best match, and confirms with user before operating on it
3. **Given** operation would fail (e.g., task not found), **When** user sends command, **Then** AI responds gracefully with explanation instead of error, suggesting alternatives

---

### User Story 4 - Access Chat via Isolated UI Route (Priority: P2)

As a user, I want to access the chat interface at a dedicated URL, so I can switch between task dashboard and chat without page refreshes or navigation conflicts.

**Why this priority**: Frontend isolation is required by Constitution. P2 because it's infrastructure rather than core functionality. Tested in frontend spec (Spec-3 doesn't cover this).

**Independent Test**: Can be fully tested by: navigate to `/chat` route, verify chat UI loads, create/send a message, verify dashboard at `/` is unaffected. Delivers: isolated chat experience.

**Acceptance Scenarios**:

1. **Given** user is authenticated, **When** user navigates to `/chat`, **Then** chat interface loads with conversation list on left, message area on right
2. **Given** user is on chat page, **When** user sends a message, **Then** message appears in chat, agent processes it, response appears, and task dashboard page (if open in another tab) is not affected
3. **Given** user has multiple tabs (one on `/` dashboard, one on `/chat`), **When** user interacts with chat, **Then** dashboard tab remains responsive and unchanged

---

### Edge Cases

- What happens when user sends a malformed command (e.g., "create task with no title")? AI should clarify what's needed instead of failing.
- What happens when user asks AI to delete a task but it belongs to another user (cross-user boundary)? MCP tool should prevent access; AI receives 401 error and informs user appropriately.
- What happens when OpenAI API is down or slow? Chat endpoint returns 503 error; frontend displays "AI service temporarily unavailable" message.
- What happens when user's JWT expires mid-conversation? Next message attempt gets 401; chat frontend redirects to Sign In.
- What happens when conversation database becomes corrupted or inaccessible? Chat endpoint returns 500; conversation history is lost until recovery (acceptable for MVP).

## Requirements

### Functional Requirements

- **FR-001**: System MUST accept chat messages via `POST /api/{user_id}/chat` endpoint requiring valid JWT authentication
- **FR-002**: System MUST extract authenticated user ID from JWT claims, never from request path parameters
- **FR-003**: System MUST store user messages in Conversation and Message database tables with user_id, conversation_id, role, and content
- **FR-004**: System MUST retrieve message history for a conversation and pass to OpenAI Agents SDK with full context
- **FR-005**: System MUST execute OpenAI Agents with MCP tools (list_tasks, get_task, create_task, update_task, delete_task, complete_task) only
- **FR-006**: System MUST enforce task ownership in MCP tool calls: tool calls inherit authenticated user_id from JWT, never trusting client input
- **FR-007**: System MUST wrap MCP tool calls around existing Phase-2 task endpoints, avoiding code duplication
- **FR-008**: System MUST store agent responses (assistant messages) in Message table with role='assistant'
- **FR-009**: System MUST return chat response with message ID, role, content, and timestamp to client
- **FR-010**: System MUST process each chat request independently without storing session state in backend memory
- **FR-011**: System MUST implement per-user rate limiting for chat requests (max 20 requests/minute per user recommended)
- **FR-012**: System MUST handle OpenAI API errors gracefully: timeout after 30 seconds, retry with exponential backoff (max 3 retries), return generic error message
- **FR-013**: System MUST provide conversation CRUD endpoints: list conversations (`GET /api/{user_id}/conversations`), get conversation (`GET /api/{user_id}/conversations/{id}`), delete conversation (`DELETE /api/{user_id}/conversations/{id}`)
- **FR-014**: System MUST ensure all conversation endpoints require JWT and enforce user ownership (404 if not owned by authenticated user)
- **FR-015**: System MUST support starting new conversation via first chat message or explicit conversation creation
- **FR-016**: System MUST index database conversations on (user_id, created_at) for performance
- **FR-017**: System MUST NOT modify Task, User, or authentication models from Phase-2
- **FR-018**: System MUST NOT expose OpenAI API keys in logs, error messages, or responses
- **FR-019**: System MUST NOT bypass phase-2 task ownership rules in MCP tool calls
- **FR-020**: System MUST NOT store any in-memory conversation state (all state in PostgreSQL)

### Key Entities

- **Conversation**: Represents a chat thread. Attributes: `id` (primary key), `user_id` (indexed, from JWT), `title` (optional), `created_at` (auto), `updated_at` (auto). Relationships: One-to-many with Message.
- **Message**: Represents a single chat message or response. Attributes: `id` (primary key), `conversation_id` (foreign key), `user_id` (indexed, denormalized for security), `role` ("user" or "assistant"), `content` (text), `created_at` (auto). Relationships: Many-to-one with Conversation.
- **MCP Tool**: Represents a function exposed to the OpenAI Agent. MCP Tools are NOT database entities but code-level abstractions. Each tool wraps a Phase-2 task service call. Example: `list_tasks` tool calls `task_service.list_tasks(session, user_id)` internally.

## Technology Stack & Dependencies

### Backend Architecture

| Component | Technology | Purpose | Notes |
|-----------|-----------|---------|-------|
| Chat Endpoint | FastAPI | Receive and process chat messages | POST `/api/{user_id}/chat` |
| AI Agent | OpenAI Agents SDK (Python) | Execute agentic reasoning | Pinned to specific model version |
| MCP Server | Official MCP SDK (Python) | Expose task tools to agent | Hosts 6 task-related tools |
| Database | Neon PostgreSQL | Persist conversations and messages | Via existing SQLModel |
| Authentication | JWT + Better Auth | Validate user identity | Same as Phase-2 |

### Installation Requirements

- `openai-agents` SDK (Python 3.11+)
- `mcp` (Official MCP SDK) (Python 3.11+)
- Existing: `fastapi`, `sqlmodel`, `python-dotenv`

### Configuration

- `OPENAI_API_KEY`: Environment variable for OpenAI API key (required)
- `OPENAI_MODEL`: Model identifier (default: "gpt-4"; example: "gpt-4-turbo")
- `CHAT_RATE_LIMIT`: Requests per minute per user (default: 20)
- `OPENAI_TIMEOUT`: Seconds to wait for OpenAI response (default: 30)

## Success Criteria

### Measurable Outcomes

- **SC-001**: Chat endpoint accepts POST request with user message and returns AI response within 30 seconds (99% of requests)
- **SC-002**: AI agent successfully calls MCP tools and completes task operations requested in natural language (e.g., "create task" → task created in DB)
- **SC-003**: Conversation history persists across user sessions (user closes browser, returns 24 hours later, sees full conversation)
- **SC-004**: All task operations initiated through chat enforce user ownership (cross-user attempts return 401, not successful cross-user access)
- **SC-005**: Backend handles stateless request processing: 10 requests from same user to different backend instances results in consistent conversation state (no in-memory caching issues)
- **SC-006**: Rate limiting prevents abuse (21st request in minute from same user returns 429, resets at next minute boundary)
- **SC-007**: OpenAI API failures (timeout, key invalid, quota exceeded) result in graceful error response (503 or appropriate HTTP status) with user-friendly message, not crash
- **SC-008**: Chat page (frontend, Spec-3) loads without errors and does not affect dashboard task list operations

### Technology-Agnostic Criteria

- All conversation and message data queryable and durable in Neon PostgreSQL
- MCP tools reuse existing Phase-2 task endpoints (zero duplication)
- No global session state; each request independently verifiable
- JWT authentication required for all chat operations
- All errors returned as JSON with `detail` field; no internal stack traces exposed

## Assumptions & Constraints

### Assumptions Made

1. **OpenAI Model Availability**: OpenAI API is accessible from backend; we'll use `gpt-4` as default but make it configurable
2. **MCP Tool Simplicity**: Initial 6 MCP tools are basic CRUD wrappers; no complex reasoning required from tools themselves
3. **Conversation Scoping**: Each conversation is independent; AI cannot access user's previous conversations (one conversation = one request context)
4. **User Capacity**: System supports single-user alpha phase; no multi-user agent conflict issues expected
5. **Message Volume**: Average conversation ≤100 messages; no optimization for 1000+ message histories (can optimize later if needed)
6. **Frontend Implementation**: Frontend team will handle chat UI routing isolation; backend assumes chat frontend won't conflict with dashboard

### Technology Constraints

- Must use **Official MCP SDK** (not custom implementations)
- Must use **OpenAI Agents SDK** (not manual API calls)
- Must use **SQLModel** for Conversation/Message models (consistent with Phase-2)
- Must use **Neon PostgreSQL** (same database as tasks; no new systems)
- Python backend must remain **Python 3.11+** compatible
- FastAPI routes must follow existing pattern: `POST /api/{user_id}/chat`, `GET /api/{user_id}/conversations`

### Out of Scope (Explicitly Forbidden)

- Voice input or speech recognition
- Image generation or image understanding
- File uploads or document processing
- Custom knowledge base fine-tuning
- Streaming chat responses (use completed messages only)
- WebSocket real-time updates (HTTP polling for MVP)
- Multi-turn branching or edit history
- Task scheduling or automation (e.g., "remind me tomorrow")
- Integration with external services (only OpenAI + existing task endpoints)
- Modifying Spec-2 task CRUD logic or endpoints
- Modifying Spec-3 frontend dashboard components

## Implementation Boundary

### In Scope (Spec-4: Backend Only)

1. **Database Models**: Create `Conversation` and `Message` SQLModel tables with proper indexing
2. **MCP Server**: Implement MCP Server exposing 6 task tools; each tool wraps Phase-2 endpoints
3. **Chat Endpoint**: Implement `POST /api/{user_id}/chat` accepting message, managing conversation context, calling OpenAI Agents, storing response
4. **Conversation CRUD**: Implement list, retrieve, delete conversation endpoints with JWT enforcement
5. **Error Handling**: Implement consistent error responses for auth, rate limit, OpenAI failures
6. **Configuration**: Add OPENAI_API_KEY, OPENAI_MODEL, CHAT_RATE_LIMIT to config
7. **Dependencies**: Add `openai-agents` and `mcp` to requirements.txt

### Out of Scope (Frontend: Spec-3, Future Specs)

- Chat UI component (implemented in Spec-3)
- Chat routing isolation at `/chat` (implemented in Spec-3)
- Message rendering and formatting (implemented in Spec-3)
- Conversation list UI (implemented in Spec-3)

## Testing Strategy

### Unit Test Scope

- MCP tool wraps task_service calls correctly (mocks task_service)
- Chat endpoint validates JWT, returns 401 if missing/invalid
- Chat endpoint enforces user_id ownership in MCP calls
- Conversation model saves and retrieves messages correctly
- Rate limiting counter increments and resets correctly

### Integration Test Scope

- End-to-end chat: send message → store in DB → call OpenAI (mock) → store response
- MCP tool calls reach task_service layer correctly
- Conversation history retrieved in chronological order
- Cross-user access attempts return 401, not data leak
- Stateless request handling: same user ID on two requests to different backend instances uses same conversation

### Manual Test Scope

- "Create a task" via chat works
- "List tasks" via chat returns formatted summary
- "Complete task X" via chat marks task complete
- OpenAI API error simulation (invalid key) returns graceful error
- JWT expiration mid-conversation blocks next request

## Deferred to Future Specs

- Voice-to-text input
- Multi-agent collaboration or swarm
- Custom training or model fine-tuning
- Persistent agent memory across separate user sessions
- Task scheduling based on agent suggestions
- Streaming responses
- Advanced NLP features
