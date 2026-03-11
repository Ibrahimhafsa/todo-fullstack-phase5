<!--
  ============================================================================
  SYNC IMPACT REPORT
  ============================================================================
  Version Change: 1.2.0 → 2.0.0 (MAJOR - Added Phase-3 AI Chatbot extension with
  Phase-2 lockdown and MCP tool governance)

  Modified Principles:
  - Principle VI (Spec-Driven Development Mandate) - expanded for Phase-3 workflow

  Added Sections (Core Principles):
  - XVI. Phase-2 Read-Only Mandate (Spec-2 lockdown)
  - XVII. Stateless Chat Architecture (Spec-4)
  - XVIII. JWT Security for Chat (Spec-4)
  - XIX. Conversation Ownership (Spec-4)
  - XX. MCP Tool Governance (Spec-4)
  - XXI. Chat-Task Integration via MCP (Spec-4)
  - XXII. Chat Frontend Isolation (Spec-4)
  - XXIII. Conversation Data Persistence (Spec-4)
  - XXIV. Chat API Error Handling (Spec-4)
  - XXV. OpenAI Integration & Configuration (Spec-4)

  Added Sections (Development Workflow):
  - Spec-4: AI Chatbot Scope
  - Spec-4 Success Criteria
  - Explicitly Forbidden (Spec-4) additions

  Removed Sections: None

  Technology Stack Additions:
  - OpenAI Agents SDK (Python)
  - MCP Server (Official SDK - Python)
  - Conversation & Message DB models

  Templates Requiring Updates:
  - .specify/templates/plan-template.md ✅ (Phase-3/4 context added to Constitution Check)
  - .specify/templates/spec-template.md ✅ (Phase-4 scope compatible)
  - .specify/templates/tasks-template.md ✅ (Phase structure compatible)

  Follow-up TODOs: None

  ============================================================================
-->

# Project Constitution: Authentication, Task Management, Frontend UI & AI Chatbot

## Overview

This constitution defines non-negotiable rules, constraints, and quality standards for:
- **Spec-1**: User authentication and identity (JWT-based)
- **Spec-2**: Task management (CRUD + ownership) — **LOCKED READ-ONLY**
- **Spec-3**: Frontend UI and responsive experience
- **Spec-4**: AI Chatbot with OpenAI Agents SDK and MCP Server

All implementation MUST comply with this constitution.

## Core Principles

### I. JWT-Only Authentication

All user authentication MUST use JSON Web Tokens (JWT) as the sole authentication
mechanism. The token flow is:

1. User authenticates via Better Auth (frontend)
2. Better Auth issues JWT with user claims
3. Frontend includes JWT in `Authorization: Bearer <token>` header
4. Backend validates JWT signature using shared secret
5. User identity extracted from JWT claims only

**Rationale**: Single authentication standard ensures consistency across the stack
and enables stateless verification.

### II. Shared Secret Synchronization

The `BETTER_AUTH_SECRET` environment variable MUST be identical in both frontend
and backend environments:

- Frontend: `.env.local` or `.env`
- Backend: `.env`

**Rules**:
- Secret MUST be at least 32 characters
- Secret MUST NOT be committed to version control
- Secret MUST be rotated if compromised
- Mismatched secrets result in authentication failure

**Rationale**: JWT signature verification requires the same secret on both sides.

### III. User Identity Trust Boundary

The backend MUST NEVER trust client-provided user identity. All user identification
MUST come from the decoded JWT token:

```python
# CORRECT: Extract user_id from JWT
user_id = get_current_user_from_jwt(token).id

# FORBIDDEN: Trust client-provided user_id
user_id = request.body.user_id  # NEVER DO THIS
```

**Rationale**: Client data can be manipulated; JWT claims are cryptographically signed.

### IV. Protected Route Enforcement

All API routes handling user data MUST require valid JWT authentication:

- Missing JWT → `401 Unauthorized`
- Invalid/expired JWT → `401 Unauthorized`
- Valid JWT → Extract user identity and proceed

**Exceptions**: Only public endpoints (health check, auth endpoints) are exempt.

**Rationale**: Defense in depth; no route should accidentally expose user data.

### V. Authentication Failure Handling

Authentication failures MUST return minimal information to prevent enumeration attacks:

- Invalid credentials → Generic "Authentication failed" message
- User not found → Same generic message (no "user does not exist")
- Rate limiting SHOULD be applied to auth endpoints

**Rationale**: Detailed error messages aid attackers in credential stuffing.

### VI. Spec-Driven Development Mandate

All implementation MUST follow the SDD workflow:

```
Constitution → Specify → Plan → Tasks → Implement
```

**Rules**:
- NO implementation without approved specification
- NO implementation without approved tasks
- Spec changes require re-approval before implementation
- Constitution violations block PR approval
- Phase-2 implementation is LOCKED (no new features, only bug fixes via ADR)
- Phase-3 and Phase-4 features require explicit spec separation

**Rationale**: Ensures security requirements are explicitly documented and reviewed.
Phase separation prevents regression and maintains stability.

### VII. Task Ownership Enforcement (Spec-2)

All task operations MUST enforce user ownership:

```python
# CORRECT: Filter by authenticated user
tasks = db.query(Task).filter(Task.user_id == current_user.id).all()

# FORBIDDEN: Trust path parameter without verification
tasks = db.query(Task).filter(Task.user_id == path_user_id).all()  # NEVER
```

**Rules**:
- The `{user_id}` path parameter MUST NOT be trusted alone
- The authenticated user MUST be derived from JWT claims
- Every DB query MUST be filtered by the authenticated user's ID
- Users MUST only view, modify, or delete their own tasks
- Cross-user access attempts MUST return `401 Unauthorized`

**Rationale**: Path parameters can be manipulated; only JWT-derived identity is trusted.

### VIII. Task Data Persistence (Spec-2)

All task data MUST be persisted in Neon PostgreSQL:

**Rules**:
- In-memory storage is FORBIDDEN for task data
- Tasks MUST survive server restarts
- Database connection MUST use environment variables (never hardcode credentials)
- SQLModel MUST be used as the ORM layer

**Rationale**: Production-grade persistence ensures data durability and enables scaling.

### IX. Task API Contract (Spec-2)

The following REST endpoints MUST be implemented:

| Method | Endpoint | Action |
|--------|----------|--------|
| GET | `/api/{user_id}/tasks` | List user's tasks |
| POST | `/api/{user_id}/tasks` | Create a new task |
| GET | `/api/{user_id}/tasks/{id}` | Get task details |
| PUT | `/api/{user_id}/tasks/{id}` | Update task |
| DELETE | `/api/{user_id}/tasks/{id}` | Delete task |
| PATCH | `/api/{user_id}/tasks/{id}/complete` | Toggle completion |

**Rules**:
- All endpoints MUST require valid JWT
- All endpoints MUST enforce ownership (Principle VII)
- Task entity MUST include: `id`, `title`, `description`, `is_complete`, `user_id`
- Timestamps (`created_at`, `updated_at`) SHOULD be included

**Rationale**: RESTful contract ensures predictable client integration.

### X. Error Response Standards (Spec-2)

All API responses MUST follow consistent patterns:

| Status | Condition |
|--------|-----------|
| `200 OK` | Successful GET, PUT, PATCH |
| `201 Created` | Successful POST |
| `204 No Content` | Successful DELETE |
| `400 Bad Request` | Invalid request body/parameters |
| `401 Unauthorized` | Missing/invalid JWT or ownership violation |
| `404 Not Found` | Task does not exist (for the authenticated user) |

**Rules**:
- Error responses MUST include a JSON body with `detail` field
- Error messages MUST NOT leak internal implementation details
- `404` MUST be returned even if task exists but belongs to another user

**Rationale**: Consistent errors simplify client error handling and prevent info leakage.

### XI. Frontend Workspace Isolation (Spec-3)

All frontend work MUST respect strict workspace boundaries:

**Rules**:
- All frontend work MUST happen ONLY inside `/frontend`
- The `/frontend-DO-NOT-TOUCH` directory MUST NEVER be modified (backup folder)
- The Next.js app MUST NOT be recreated; use existing structure
- Auth components that already exist MUST NOT be duplicated
- Before editing any file, MUST verify it doesn't already exist elsewhere

**Rationale**: Prevents accidental corruption of backup code and duplicate implementations.

### XII. Design System Compliance (Spec-3)

All UI components MUST adhere to the established design system:

**Required Visual Theme**:
- Background: soft black/dark base with teal/cyan glow accents
- Cards: glassy (semi-transparent), blur effect, `rounded-xl`
- Buttons: modern appearance with soft glow on hover
- Inputs: clean, high-contrast with visible focus ring
- Smooth hover transitions on all interactive elements

**Rules**:
- Styling MUST use Tailwind CSS utility classes only
- Inline CSS is FORBIDDEN
- UI MUST appear premium, modern, and hackathon-demo ready
- Custom CSS files are allowed only for Tailwind configuration

**Rationale**: Consistent visual language creates professional user experience.

### XIII. Responsive Layout Requirements (Spec-3)

All pages MUST be fully responsive across device sizes:

**Rules**:
- Mobile-first breakpoints MUST be applied (sm → md → lg → xl)
- Layout MUST NOT break on viewports 320px to 2560px wide
- Touch targets MUST be minimum 44x44px on mobile
- Text MUST remain readable without horizontal scrolling
- No layout shifts or flash of unstyled content (FOUC)

**Rationale**: Ensures usability across all devices for demo and production use.

### XIV. UX State Management (Spec-3)

All data-driven pages MUST handle loading, empty, and error states:

**Required States**:
- **Loading State**: Visual indicator while data is being fetched
- **Empty State**: Clear messaging when no data exists (e.g., "No tasks yet")
- **Error State**: User-friendly error message with retry option

**Rules**:
- States MUST be visually distinct and on-theme
- Loading indicators MUST appear within 100ms of request initiation
- Error messages MUST NOT expose technical details
- Retry actions MUST be obvious and accessible

**Rationale**: Prevents user confusion and ensures graceful handling of edge cases.

### XV. Frontend-Backend Integration (Spec-3)

All frontend API calls MUST follow integration rules:

**Rules**:
- Every API request MUST include JWT token in Authorization header
- If API returns `401 Unauthorized` → redirect to Sign In page
- API base URL MUST be configured via environment variable
- No backend modifications are allowed in Spec-3
- No direct database access from frontend

**Rationale**: Ensures secure, consistent communication with backend services.

### XVI. Phase-2 Read-Only Mandate

All Phase-2 (Task Management) code is LOCKED for new feature development:

**Rules**:
- NO modifications to existing task CRUD endpoints
- NO schema changes to Task or User models
- NO changes to authentication logic
- Bug fixes ONLY if documented in ADR with security impact analysis
- Breaking changes to task logic are FORBIDDEN
- All task-related code references MUST be preserved
- New Phase-3/4 features MUST use existing task endpoints via MCP

**Exceptions**:
- Security patches (with ADR documentation)
- Bug fixes (with detailed justification)
- Dependencies updates (with compatibility verification)

**Rationale**: Phase-2 is production-stable. Phase-3/4 extend via composition,
not modification. Prevents regression and data loss.

### XVII. Stateless Chat Architecture (Spec-4)

The AI Chat system MUST operate with stateless backend design:

**Rules**:
- Each chat request MUST be independently verifiable
- No session state stored in backend memory
- User context extracted from JWT on every request
- Conversation history stored in database, not in-memory caches
- OpenAI Agents SDK interactions MUST NOT accumulate server-side state
- Load balancing across multiple backend instances MUST be possible

**Stateless Pattern**:
```python
# CORRECT: Every request is independent
@app.post("/api/chat")
def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    conversation = db.get(Conversation, user_id=current_user.id)
    response = agent.process(request.message, conversation_history)
    return response

# FORBIDDEN: Server-side session storage
global_conversations = {}  # NEVER DO THIS
```

**Rationale**: Enables horizontal scaling, fault tolerance, and prevents memory leaks.

### XVIII. JWT Security for Chat (Spec-4)

All chat endpoints MUST enforce JWT authentication with explicit user verification:

**Rules**:
- Every chat endpoint MUST require valid JWT
- User ID MUST be extracted from JWT claims only
- Chat requests with missing/invalid JWT → `401 Unauthorized`
- Cross-user chat access attempts → `401 Unauthorized`
- Chat context MUST NOT be accessible cross-user

**Chat Endpoint Examples**:
```
POST /api/{user_id}/chat/message        - Send message (requires JWT)
GET  /api/{user_id}/conversations       - List conversations (requires JWT)
GET  /api/{user_id}/conversations/{id}  - Get conversation (requires JWT)
DELETE /api/{user_id}/conversations/{id} - Delete conversation (requires JWT)
```

**Rationale**: Ensures chat data is not exposed between users and integrates
with existing auth infrastructure.

### XIX. Conversation Ownership (Spec-4)

All conversation operations MUST enforce strict user ownership:

**Rules**:
- Each Conversation entity MUST have an immutable `user_id` field
- Every DB query MUST filter by authenticated user's ID
- Users MUST only view, modify, or delete their own conversations
- Users MUST only access messages in their own conversations
- Cross-user access attempts MUST return `401 Unauthorized` (not 404)
- Conversation IDs MUST NOT reveal ownership across users

**Database Schema**:
```python
class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    user_id: str = Field(index=True, nullable=False)  # From JWT
    title: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Rationale**: Prevents accidental data leakage between users; mirrors task ownership model.

### XX. MCP Tool Governance (Spec-4)

The MCP Server MUST expose only explicitly approved tools:

**Allowed MCP Tools (Explicit Allowlist)**:
- `list_tasks` - Fetch user's tasks (calls existing Spec-2 Task endpoint)
- `get_task` - Fetch single task (calls existing Spec-2 Task endpoint)
- `create_task` - Create task (calls existing Spec-2 Task endpoint)
- `update_task` - Update task (calls existing Spec-2 Task endpoint)
- `delete_task` - Delete task (calls existing Spec-2 Task endpoint)
- `complete_task` - Toggle task completion (calls existing Spec-2 Task endpoint)

**Forbidden MCP Tools**:
- Direct database access
- File system operations
- System command execution
- Network requests outside of approved endpoints
- Direct interaction with Better Auth
- OpenAI API calls (only via agent SDK)

**MCP Implementation Pattern**:
```python
# CORRECT: MCP tool wraps existing REST endpoint
@mcp_tool
def list_tasks(user_id: str):
    # Call internal task endpoint with user_id from JWT
    return get_tasks_by_user(user_id)

# FORBIDDEN: Direct DB access in MCP tool
@mcp_tool
def list_tasks_direct():
    return db.query(Task).all()  # NEVER DO THIS
```

**Rules**:
- All tools MUST validate user ownership before executing
- Tools MUST NOT bypass existing REST endpoints
- Tool responses MUST be deterministic and idempotent
- MCP Server MUST run in sandboxed environment

**Rationale**: Maintains security boundary, prevents privilege escalation,
ensures auditability through existing REST API.

### XXI. Chat-Task Integration via MCP (Spec-4)

Task management from chat MUST reuse existing Spec-2 endpoints:

**Rules**:
- Chat agent MUST use MCP tools to interact with tasks
- NO direct database modifications from chat context
- NO bypassing of task ownership rules
- MCP tools MUST enforce same JWT-based ownership
- Chat operations on tasks MUST be logged to task audit trail
- Task changes initiated by chat MUST be attributable to user

**Chat-to-Task Flow**:
```
User Message → OpenAI Agent → MCP Tool Call → REST API → DB
                                    ↓
                         (Authorization check)
                         (Ownership verification)
```

**Rationale**: Single source of truth for task logic; chat is client,
not backend. Enables consistent audit trail and compliance.

### XXII. Chat Frontend Isolation (Spec-4)

Chat UI components MUST NOT interfere with existing dashboard:

**Rules**:
- Chat UI MUST be implemented in separate route/page (e.g., `/chat`)
- Dashboard at `/` MUST continue to work independently
- Chat and Task Dashboard MUST NOT share component tree
- No global state modifications that affect task display
- Chat state MUST be isolated to chat page only
- Router isolation MUST be enforced (separate layouts if needed)

**Forbidden Chat Frontend Patterns**:
- Modifying task list display from chat page
- Sharing state managers between chat and dashboard
- Reusing task components in chat without wrapper isolation
- Cross-page context providers

**Rationale**: Prevents regression of Spec-3 (Dashboard). Chat is
additive feature, not replacement for existing UI.

### XXIII. Conversation Data Persistence (Spec-4)

All conversation and message data MUST be persisted in Neon PostgreSQL:

**Rules**:
- In-memory storage is FORBIDDEN for conversations
- Conversations MUST survive server restarts
- Message history MUST be queryable by conversation ID
- Database connection MUST use environment variables
- SQLModel MUST be used for Conversation and Message models
- Indexes MUST exist on `(user_id, created_at)` for performance

**Database Schema Requirements**:
```python
class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    user_id: str = Field(index=True, nullable=False)
    title: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Message(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id")
    user_id: str = Field(index=True, nullable=False)  # Denormalized for security
    role: str = Field(default="user")  # "user" or "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**Rationale**: Production-grade persistence; enables conversation replay,
audit trails, and recovery.

### XXIV. Chat API Error Handling (Spec-4)

Chat endpoints MUST follow consistent error response patterns:

**Error Status Codes**:
| Status | Condition |
|--------|-----------|
| `200 OK` | Successful chat message |
| `201 Created` | New conversation created |
| `400 Bad Request` | Invalid message format or parameters |
| `401 Unauthorized` | Missing/invalid JWT or ownership violation |
| `404 Not Found` | Conversation not found (for authenticated user) |
| `429 Too Many Requests` | Rate limit exceeded |
| `503 Service Unavailable` | OpenAI API unavailable |

**Rules**:
- Error responses MUST include `detail` field with user-friendly message
- MUST NOT expose OpenAI API keys or internal tokens
- MUST NOT leak conversation data in error messages
- Errors MUST NOT reveal whether conversation belongs to another user
- Rate limiting MUST be enforced per user (not global)
- OpenAI service errors MUST be wrapped with generic "AI service unavailable"

**Rationale**: Consistent errors enable client error handling and prevent
information leakage. Rate limiting prevents abuse.

### XXV. OpenAI Integration & Configuration (Spec-4)

OpenAI Agents SDK integration MUST be secure and configurable:

**Rules**:
- OpenAI API key MUST be stored in environment variable (never hardcoded)
- API key MUST NOT appear in logs, error messages, or responses
- OpenAI model MUST be configurable via environment variable
- Model MUST be pinned to specific version (e.g., `gpt-4` not `latest`)
- Timeout for OpenAI API calls MUST be set (recommended: 30 seconds)
- Retry logic MUST be implemented with exponential backoff
- OpenAI calls MUST include user context in system prompt for logging

**Configuration Pattern**:
```python
from app.config import settings

openai_api_key = settings.OPENAI_API_KEY  # From .env
model = settings.OPENAI_MODEL  # Default: "gpt-4"
timeout = 30  # seconds

# System prompt MUST include user context
system_prompt = f"""You are a task assistant for user {user_id}.
You can help manage tasks using available tools.
Be concise and helpful."""
```

**Rationale**: Secures sensitive credentials, enables model switching for cost control,
ensures visibility into OpenAI interactions for auditing.

## Technology Constraints

This constitution applies to the following technology stack:

| Layer | Technology | Role |
|-------|------------|------|
| Frontend | Next.js 16+ (App Router) | Better Auth client, JWT storage, UI |
| Frontend (Chat) | Next.js 16+ (OpenAI ChatKit) | Chat UI integration |
| Styling | Tailwind CSS | Utility-first styling |
| Auth Library | Better Auth | JWT issuance, session management |
| Backend | FastAPI (Python 3.11+) | JWT verification, API endpoints |
| ORM | SQLModel | Database operations |
| Database | Neon Serverless PostgreSQL | Persistent storage |
| AI Engine | OpenAI Agents SDK | Chat agent execution |
| MCP | MCP Server (Official SDK) | Tool exposure to agent |
| Transport | HTTPS | Secure transmission |

**Stack-Specific Rules**:
- Better Auth MUST be configured with JWT session strategy
- FastAPI MUST use dependency injection for auth (`Depends(get_current_user)`)
- Tokens MUST be transmitted via Authorization header (not cookies for API)
- SQLModel MUST be used for all database models (Task, User, Conversation, Message)
- Database credentials MUST be loaded from environment variables
- Tailwind CSS MUST be used for all styling (no inline CSS)
- OpenAI Agents SDK MUST be Python 3.11+ compatible
- MCP Server MUST use official MCP SDK (not custom implementations)
- Chat frontend MUST use OpenAI ChatKit for message rendering

## Development Workflow

### Spec-1: Authentication Scope

This constitution governs:
- User signup flow
- User signin flow
- JWT token issuance (Better Auth)
- JWT token verification (FastAPI)
- Shared secret configuration
- User identity extraction from JWT
- Authentication failure handling
- Protected route middleware

### Spec-2: Task Management Scope (READ-ONLY)

This constitution governs:
- Task CRUD operations (Create, Read, Update, Delete)
- Task completion toggle
- Task ownership enforcement
- Task persistence in Neon PostgreSQL
- Task API endpoint contracts

**STATUS: LOCKED** — No new features. Bug fixes only via ADR.
All Phase-3/4 features MUST use existing endpoints via MCP tools.

### Spec-3: Frontend UI Scope

This constitution governs:
- Auth pages (signin, signup) styling and UX
- Protected Task Dashboard implementation
- Task CRUD UI components:
  - Create task form
  - Task list display
  - Update task functionality
  - Delete task confirmation
  - Toggle completion interaction
- Responsive layout (mobile/tablet/desktop)
- Design system implementation (teal–cyan–black glow theme)
- Loading, empty, and error state handling
- Frontend-backend API integration

### Spec-4: AI Chatbot Scope

This constitution governs:
- Chat page layout and routing (isolated from dashboard)
- Chat message input/display UI using OpenAI ChatKit
- Conversation list and management
- OpenAI Agents SDK integration with MCP tools
- MCP Server tool definitions (task-related only)
- Conversation and Message database models
- Chat endpoint implementation (`POST /api/{user_id}/chat/message`)
- Conversation endpoints (list, retrieve, delete)
- Error handling for chat and OpenAI failures
- JWT validation for all chat endpoints
- Stateless chat processing
- Rate limiting for chat requests

### Explicitly Forbidden

The following are OUT OF SCOPE for this constitution:

**Forbidden in Spec-2 (LOCKED)**:
- Any modifications to existing task endpoints
- Changes to Task or User schema
- Authentication logic changes

**Forbidden in Spec-3 (Phase-2 Dashboard)**:
- Search/filter/sort functionality
- Tags or priorities
- Due dates or reminders
- Recurring tasks
- Backend modifications
- Database changes
- New Next.js app creation
- Editing `/frontend-DO-NOT-TOUCH`
- Duplicating existing auth components

**Forbidden in Spec-4 (Chat)**:
- Advanced features beyond basic chat (voice, images, file uploads)
- Custom knowledge bases or fine-tuning
- Streaming responses (use completed messages only)
- Multi-turn branching/edit history
- Task scheduling or automation
- Integration with external services
- Custom MCP tools beyond task CRUD
- Modifying existing dashboard components
- Storing chat state in frontend localStorage without DB backup
- Direct API calls to OpenAI (only via agents SDK)
- WebSocket connections (HTTP polling only)

**Deferred to Future Specs**:
- Task sharing/collaboration
- Multi-user task boards
- Task comments or attachments
- Real-time updates
- Offline support
- Voice commands
- Image generation
- Custom agent personalities

### Spec-1 Success Criteria

Authentication implementation is complete when:
- [ ] Users can sign up with email/password
- [ ] Users can sign in and receive JWT
- [ ] JWT is correctly validated by backend
- [ ] Backend correctly identifies authenticated user from JWT
- [ ] Unauthorized access returns 401
- [ ] User data isolation is enforced

### Spec-2 Success Criteria (FROZEN)

Task Management implementation is complete when:
- [ ] All CRUD endpoints work correctly
- [ ] Toggle completion endpoint works
- [ ] Data is persisted in Neon PostgreSQL
- [ ] Ownership rules are enforced for every request
- [ ] Unauthorized access returns 401
- [ ] Non-existent tasks return 404
- [ ] Response formats are consistent

**Status**: ✅ COMPLETE AND LOCKED

### Spec-3 Success Criteria

Frontend UI implementation is complete when:
- [ ] UI displays modern teal/cyan/black glowing theme
- [ ] Dashboard is fully responsive (mobile + tablet + desktop)
- [ ] Task CRUD works end-to-end from UI
- [ ] Loading states display during API calls
- [ ] Empty state shows when no tasks exist
- [ ] Error states display with retry option
- [ ] 401 responses redirect to Sign In
- [ ] No duplicate files were created
- [ ] No edits made to `/frontend-DO-NOT-TOUCH`

### Spec-4 Success Criteria

AI Chatbot implementation is complete when:
- [ ] Users can access chat at isolated route (e.g., `/chat`)
- [ ] Chat messages are sent to OpenAI Agents via MCP tools
- [ ] Conversation history is persisted in Neon PostgreSQL
- [ ] Users can only access their own conversations
- [ ] JWT is required for all chat endpoints
- [ ] Chat page does not affect dashboard display or state
- [ ] MCP tools only expose task CRUD operations
- [ ] Ownership rules enforced for task operations from chat
- [ ] Error states display for OpenAI API failures
- [ ] Rate limiting prevents abuse (max N requests/min per user)
- [ ] No conversations or messages leaked between users
- [ ] Chat state is stateless on backend (no in-memory caches)
- [ ] All conversation data queryable and durable in database

## Governance

### Amendment Process

1. Propose change with rationale
2. Document security impact analysis
3. Update version following semver:
   - MAJOR: Principle removal, redefinition, or phase lockdown
   - MINOR: New principle, expanded guidance, or phase extension
   - PATCH: Clarifications, typo fixes, non-semantic refinements
4. Update dependent templates if affected
5. Create PHR in `history/prompts/constitution/`
6. Commit with message: `docs: amend constitution to vX.Y.Z (<summary>)`

### Compliance Review

- All PRs MUST be verified against this constitution
- Authentication, Task Management (Spec-2), Frontend UI, and Chat changes require explicit constitution check
- Phase-2 modifications require special justification and ADR
- Violations MUST be resolved before merge
- Security exceptions require documented justification and ADR

### Supersession

This constitution supersedes all other authentication, task management, frontend UI,
and chat guidance in the project. When conflicts arise, this document takes precedence.

**Version**: 2.0.0 | **Ratified**: 2026-01-11 | **Last Amended**: 2026-02-18
