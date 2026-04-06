<!--
  ============================================================================
  SYNC IMPACT REPORT
  ============================================================================
  Version Change: 2.0.0 → 3.0.0 (MAJOR - Added Phases 5-7 with event-driven
  architecture, Dapr integration, cloud deployment, and advanced features)

  Modified Principles:
  - Principle VI (Spec-Driven Development Mandate) - expanded for Phases 5-7
  - Principle XVII (Stateless Chat Architecture) - extended for event sourcing

  Added Sections (Core Principles):
  - XXVI. Event-Driven Architecture (Phase 6 - 007-local-event-architecture)
  - XXVII. Kafka Event Bus Integration (Phase 6)
  - XXVIII. Dapr Pub/Sub Abstraction (Phase 6)
  - XXIX. Event Sourcing Pattern (Phase 6)
  - XXX. Message Schema & Versioning (Phase 6)
  - XXXI. Local Kubernetes Event Mesh (Phase 6)
  - XXXII. Cloud Deployment Portability (Phase 7 - 008-cloud-deployment)
  - XXXIII. Helm Chart Reusability (Phase 7)
  - XXXIV. Cloud Provider Abstraction (Phase 7)
  - XXXV. Advanced Chat Features (Phase 5 - 006-advanced-features)
  - XXXVI. Conversation Intelligence (Phase 5)
  - XXXVII. Chat Analytics & Observability (Phase 5)

  Added Sections (Development Workflow):
  - Spec-5: Advanced Features Scope (006-advanced-features)
  - Spec-6: Event Architecture Scope (007-local-event-architecture)
  - Spec-7: Cloud Deployment Scope (008-cloud-deployment)
  - Spec-5/6/7 Success Criteria
  - Explicitly Forbidden (Specs 5-7) additions

  Removed Sections: None

  Technology Stack Additions:
  - Apache Kafka (message bus)
  - Dapr (service mesh for pub/sub abstraction)
  - Cloud providers (AWS, Azure, GCP - abstracted via Helm)
  - Prometheus & Grafana (observability)
  - Jaeger (distributed tracing)
  - Event schema registry (Avro/JSON)

  Templates Requiring Updates:
  - .specify/templates/plan-template.md ⚠ (Constitution Check updated)
  - .specify/templates/spec-template.md ⚠ (New phase scope sections needed)
  - .specify/templates/tasks-template.md ⚠ (Event-driven task types added)
  - .specify/templates/checklist-template.md ⚠ (New checklists for events)

  Follow-up TODOs: None

  ============================================================================
-->

# Project Constitution: Authentication, Task Management, Chat, Advanced Features, Events & Cloud

## Overview

This constitution defines non-negotiable rules, constraints, and quality standards for:
- **Spec-1**: User authentication and identity (JWT-based)
- **Spec-2**: Task management (CRUD + ownership) — **LOCKED READ-ONLY**
- **Spec-3**: Frontend UI and responsive experience
- **Spec-4**: AI Chatbot with OpenAI Agents SDK and MCP Server
- **Spec-5**: Advanced Chat Features (006-advanced-features)
- **Spec-6**: Event-Driven Architecture (007-local-event-architecture)
- **Spec-7**: Cloud Deployment (008-cloud-deployment)

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
- Phases 3-7 features require explicit spec separation
- Phase 5-7 features MUST NOT break existing functionality in Phases 1-4

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

**Rationale**: Phase-2 is production-stable. Phases 3-7 extend via composition,
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
- Event-driven chat MUST NOT accumulate state in-memory (use event log)

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

### XXVI. Event-Driven Architecture (Spec-6)

The system MUST support asynchronous communication via events:

**Rules**:
- All state-changing operations (task creation, completion, deletion) MUST emit events
- Events MUST be immutable records of what happened (not state snapshots)
- Events MUST include: `type`, `user_id`, `resource_id`, `timestamp`, `data`
- Events MUST be published to message broker (Kafka via Dapr)
- Event consumers MUST be idempotent (safe to replay)
- No operation MUST be blocked waiting for event consumption
- Event processing failures MUST NOT corrupt primary data

**Event Types (examples)**:
```
TaskCreated(user_id, task_id, title, description)
TaskCompleted(user_id, task_id)
TaskUpdated(user_id, task_id, title, description)
TaskDeleted(user_id, task_id)
ConversationStarted(user_id, conversation_id)
MessageReceived(user_id, conversation_id, message_id)
```

**Rationale**: Events enable loose coupling, audit trails, and integration
with external systems without direct dependencies.

### XXVII. Kafka Event Bus Integration (Spec-6)

Kafka MUST be the primary message bus for events:

**Rules**:
- Kafka topics MUST be organized by domain (e.g., `tasks`, `conversations`)
- Topic names MUST follow pattern: `{domain}.{event_type}.{version}`
  Example: `tasks.task_created.v1`, `conversations.message_received.v1`
- Partitioning MUST be by `user_id` to ensure ordering per user
- Retention policy MUST be at least 7 days (configurable)
- Event schema MUST be registered in schema registry (Avro or JSON)
- Consumer groups MUST be used for distributed consumption
- Offset tracking MUST be maintained per consumer group

**Forbidden Patterns**:
- Direct Kafka clients in FastAPI endpoints (use Dapr)
- Multiple topics for same event type (single source of truth)
- Consumer lag MUST NOT exceed 1 hour during normal operation
- Manual offset management (use Dapr or consumer group offset tracking)

**Rationale**: Kafka ensures durability, ordering, and replay capability.
Event-driven patterns enable scalability and decoupling.

### XXVIII. Dapr Pub/Sub Abstraction (Spec-6)

Dapr MUST be the abstraction layer for all pub/sub operations:

**Rules**:
- All event publishing MUST use Dapr Pub/Sub API (not direct Kafka client)
- Dapr state management MUST be used for distributed state
- Dapr secrets management MUST be used for sensitive values (API keys)
- Dapr bindings MUST be used for external service integrations
- Service-to-service calls MUST use Dapr service invocation (not REST)
- All Dapr calls MUST include retries and timeout configuration

**Dapr Configuration**:
```yaml
# Dapr pub/sub component (kafka)
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "kafka:9092"
```

**Backend Code Pattern**:
```python
# Publishing via Dapr (not direct Kafka)
import dapr.client

with dapr.client.DaprClient() as d:
    d.publish_event(
        pubsub_name="pubsub",
        topic_name="tasks.task_created.v1",
        data=json.dumps(event),
    )
```

**Rationale**: Dapr abstracts message broker implementation. Enables
switching from Kafka to RabbitMQ, Azure Service Bus, etc. without code changes.

### XXIX. Event Sourcing Pattern (Spec-6)

Event sourcing MUST be the pattern for audit trail and recovery:

**Rules**:
- Original state (task, conversation) MUST be stored in database
- All mutations MUST generate immutable events
- Events MUST be appended to event log (not updated or deleted)
- Event log MUST be queryable for audit and debugging
- Snapshots MAY be created for performance (read models)
- Current state MUST be derivable by replaying events from start
- Deletion MUST emit a `{Resource}Deleted` event (no physical deletion)

**Event Log Storage**:
```python
class EventLog(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    user_id: str = Field(index=True, nullable=False)
    aggregate_id: str  # task_id or conversation_id
    aggregate_type: str  # "Task" or "Conversation"
    event_type: str  # "Created", "Updated", "Deleted"
    data: str  # JSON event data
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: int  # Event sequence number per aggregate
```

**Rationale**: Event sourcing provides complete audit trail, enables
temporal queries ("what was the state at 2pm?"), and aids debugging.

### XXX. Message Schema & Versioning (Spec-6)

All events MUST follow strict schema and versioning:

**Rules**:
- Events MUST be serialized as JSON with consistent structure
- Event schema MUST be registered (Avro or JSON Schema)
- Schema MUST include: `type`, `version`, `user_id`, `timestamp`
- All fields MUST have type hints (not `any` or `object`)
- Breaking changes MUST increment major version (v1 → v2)
- New topics MUST be created for major versions (not reusing old topic)
- Schema evolution MUST follow compatibility rules (backward/forward)
- Consumer MUST handle events from multiple schema versions

**Event Schema Example**:
```json
{
  "type": "TaskCreated",
  "version": "1.0",
  "user_id": "user123",
  "timestamp": "2026-03-15T10:30:00Z",
  "task_id": 42,
  "title": "Buy groceries",
  "description": "Get milk and eggs"
}
```

**Rationale**: Versioning enables schema evolution without breaking consumers.
Strict typing prevents data corruption and enables validation.

### XXXI. Local Kubernetes Event Mesh (Spec-6)

Local development MUST use containerized Kafka within Kubernetes:

**Rules**:
- Kafka MUST run as a StatefulSet in local Kubernetes cluster
- Zookeeper (or KRaft mode) MUST be configured for consensus
- Kafka service MUST be accessible at `kafka.default.svc.cluster.local:9092`
- Dapr sidecar MUST run in every pod that publishes/consumes events
- Dapr configuration MUST reference Kafka broker address
- PersistentVolumes MUST back Kafka StatefulSet for data durability
- Helm charts MUST include Kafka setup (or reference subchart)

**Helm Kafka Subchart Pattern**:
```yaml
dependencies:
  - name: kafka
    version: "28.0.0"
    repository: "https://charts.bitnami.com/bitnami"
    alias: kafka
```

**Rationale**: Local event mesh enables development/testing of event-driven
features without external dependencies.

### XXXII. Cloud Deployment Portability (Spec-7)

All deployments (local, cloud) MUST use identical Helm charts:

**Rules**:
- Single Helm chart MUST support local Kubernetes and all cloud providers
- Environment-specific values MUST be in `values-{env}.yaml` files
  Example: `values-local.yaml`, `values-aws.yaml`, `values-azure.yaml`
- Cloud provider specifics MUST be abstracted via values (not conditional code)
- No provider-specific containers or sidecars (use Dapr for abstraction)
- Database connection strings MUST be injected via values (not hardcoded)
- Secrets MUST be managed by cloud provider secret stores (AWS Secrets Manager, etc.)

**Helm Values Pattern**:
```yaml
# values-local.yaml
database:
  url: "postgresql://localhost:5432/todo"
kafka:
  brokers: "kafka.default.svc.cluster.local:9092"
dapr:
  enabled: true
  pubsub: "kafka"

# values-aws.yaml
database:
  url: "postgresql://aws-rds-endpoint:5432/todo"
kafka:
  brokers: "aws-msk-endpoint:9092"
dapr:
  enabled: true
  pubsub: "azure-service-bus"  # Dapr handles cloud provider swap
```

**Rationale**: Single chart reduces maintenance, ensures consistent
deployment process across environments.

### XXXIII. Helm Chart Reusability (Spec-7)

Existing Helm charts MUST be extended for new services:

**Rules**:
- NO new Helm charts for new features (extend existing `todo-chatbot` chart)
- Subcharts (dependencies) MUST be used for third-party services (Kafka, etc.)
- Chart MUST parameterize all environment-specific values
- Chart MUST support blue-green and canary deployments
- ConfigMaps MUST be used for non-sensitive config (Dapr settings)
- Secrets MUST be used for sensitive values (API keys)
- Template names MUST follow pattern: `{service}-{resource-type}.yaml`
  Example: `backend-deployment.yaml`, `kafka-statefulset.yaml`

**Chart Directory Structure**:
```
todo-chatbot/
├── Chart.yaml
├── values.yaml
├── values-local.yaml
├── values-aws.yaml
├── charts/  # Subcharts
│   └── kafka/  # Bitnami Kafka subchart
├── templates/
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── kafka-statefulset.yaml  # Or use subchart
│   ├── dapr-config.yaml
│   └── ...
```

**Rationale**: Chart reusability reduces duplication, enables consistent
configuration management across environments.

### XXXIV. Cloud Provider Abstraction (Spec-7)

Cloud provider specifics MUST be abstracted via configuration:

**Rules**:
- NO provider-specific code (use Dapr for pub/sub, secrets, state)
- Container images MUST be provider-agnostic (no GCR, ECR URLs in Helm)
- Image registries MUST be injected via values (imagePullSecrets)
- Storage classes MUST be parameterized (not hardcoded `gp2` or `managed-premium`)
- Ingress MUST use standard Kubernetes Ingress (not provider-specific resources)
- DNS names MUST be injected via values (not hardcoded domain)
- TLS certificates MUST be managed by cloud provider (cert-manager or native)

**Cloud Provider Abstraction Pattern**:
```yaml
# Dapr component for pub/sub (provider-agnostic)
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.{{ .Values.dapr.pubsub }}  # "kafka", "azure-service-bus", etc.
  version: v1
  metadata:
  - name: brokers
    value: "{{ .Values.kafka.brokers }}"

# Result: Same Helm chart works on AWS (Kafka) or Azure (Service Bus)
```

**Rationale**: Abstraction enables multi-cloud strategy, reduces vendor lock-in,
simplifies cloud migration.

### XXXV. Advanced Chat Features (Spec-5)

Chat enhancements MUST NOT break existing chat functionality:

**Rules**:
- All new chat features MUST be backward compatible
- Existing conversation schema MUST NOT change (add new tables if needed)
- Chat API contract MUST remain unchanged (add new endpoints, don't modify old)
- New features MUST be toggleable via feature flags or config
- Rate limiting MUST adapt to new features (e.g., higher for premium users)
- All new features MUST emit events for audit trail

**Allowed Advanced Features (examples)**:
- Conversation history search
- Message filtering and sorting
- Conversation tagging/labeling
- User feedback on AI responses
- Conversation export/download
- Typing indicators
- Read receipts

**Forbidden Enhancements**:
- Schema changes to existing Conversation or Message tables
- Removal of existing endpoints
- Breaking changes to message format
- Direct integration with external services (must use MCP tools)

**Rationale**: Backward compatibility ensures existing clients continue
to work. Feature flags enable gradual rollout.

### XXXVI. Conversation Intelligence (Spec-5)

Advanced features MAY include conversation analysis and summarization:

**Rules**:
- Conversation summaries MUST be stored in database (not computed on demand)
- Summaries MUST be updated via event (when conversation ends)
- Summary generation MUST use OpenAI API (via agent SDK)
- Summary MUST NOT expose other users' conversations
- Summaries MUST be queryable for search/filtering
- Summary updates MUST NOT delay message sending

**Conversation Intelligence Examples**:
- Auto-generated title (first 50 chars or summary)
- Conversation topic classification
- Sentiment analysis of user messages
- Action items extracted from conversation

**Rationale**: Summarization improves UX (better conversation discovery),
enables analytics, and supports future intelligence features.

### XXXVII. Chat Analytics & Observability (Spec-5)

Advanced monitoring MUST be in place for chat operations:

**Rules**:
- All chat operations MUST emit structured logs (JSON format)
- Logs MUST include: timestamp, user_id, conversation_id, event_type, duration
- Metrics MUST be exported to Prometheus (message count, latency, errors)
- Traces MUST be exported to Jaeger (for debugging slow operations)
- Performance metrics MUST be tracked (OpenAI API latency, MCP tool latency)
- User PII MUST NOT be logged (only user_id, never email or message content)
- Log retention MUST comply with data privacy laws (configurable)

**Observable Metrics**:
- `chat_messages_total` - Total messages sent (by role: user/assistant)
- `chat_message_latency_seconds` - OpenAI response time
- `chat_errors_total` - Rate limit, API, and validation errors
- `mcp_tool_calls_total` - MCP tool execution count
- `mcp_tool_latency_seconds` - MCP tool execution time

**Rationale**: Observability enables debugging, performance monitoring,
and compliance with security requirements.

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
| Message Bus | Apache Kafka | Event publishing and consumption |
| Dapr | Dapr (v1.10+) | Service mesh for pub/sub, secrets, state |
| Event Schema | Avro or JSON Schema | Event serialization and validation |
| Container Orchestration | Kubernetes 1.26+ | Local and cloud deployment |
| IaC | Helm 3.10+ | Chart-based deployment |
| Monitoring | Prometheus + Grafana | Metrics and dashboards |
| Tracing | Jaeger | Distributed tracing |
| Transport | HTTPS | Secure transmission |

**Stack-Specific Rules**:
- Better Auth MUST be configured with JWT session strategy
- FastAPI MUST use dependency injection for auth (`Depends(get_current_user)`)
- Tokens MUST be transmitted via Authorization header (not cookies for API)
- SQLModel MUST be used for all database models
- Database credentials MUST be loaded from environment variables
- Tailwind CSS MUST be used for all styling (no inline CSS)
- OpenAI Agents SDK MUST be Python 3.11+ compatible
- MCP Server MUST use official MCP SDK (not custom implementations)
- Chat frontend MUST use OpenAI ChatKit for message rendering
- Kafka topics MUST be versioned and schema-registered
- Dapr sidecars MUST be injected in all pods
- Prometheus scrape intervals MUST be 15s (configurable)
- Helm charts MUST support both local K8s and cloud providers

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
All Phase-3/4/5+ features MUST use existing endpoints via MCP tools.

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

### Spec-5: Advanced Chat Features Scope (006-advanced-features)

This constitution governs:
- Conversation search and filtering
- Conversation tagging and labeling
- Conversation summaries and titles
- Message feedback (thumbs up/down)
- Conversation export/sharing (within user context)
- Typing indicators and read receipts
- Chat analytics dashboard (user's own stats)
- Feature flags for gradual rollout

**Rules**:
- MUST NOT modify existing Conversation or Message schema
- MUST NOT break existing chat endpoints
- MUST emit events for all state changes
- MUST use event-driven architecture
- New tables OK (ConversationTag, UserFeedback, etc.)
- Feature flags MUST control new functionality

### Spec-6: Event-Driven Architecture Scope (007-local-event-architecture)

This constitution governs:
- Event emission from task and conversation services
- Event schema definition and versioning
- Kafka topic structure and partitioning
- Event consumer implementation
- Dapr Pub/Sub integration
- Event sourcing for audit trails
- Local Kubernetes Kafka deployment
- Consumer group management

**Rules**:
- All state changes MUST emit events
- Events MUST be immutable and append-only
- NO event deletion or modification (only new events)
- Consumers MUST be idempotent
- Event processing failures MUST NOT corrupt data
- Kafka topics MUST be parameterized in Helm charts

### Spec-7: Cloud Deployment Scope (008-cloud-deployment)

This constitution governs:
- Helm chart extension for multi-cloud support
- Environment-specific values files
- Cloud provider abstraction (Dapr, native services)
- Secret management (cloud provider vaults)
- Database migration to managed services (RDS, Azure Database, Cloud SQL)
- Container registry configuration
- Load balancer and ingress configuration
- Monitoring and logging in cloud environments

**Supported Cloud Providers**:
- AWS (EC2/EKS, RDS, Kafka MSK, Secrets Manager)
- Azure (AKS, Database for PostgreSQL, Event Hubs, Key Vault)
- Google Cloud (GKE, Cloud SQL, Pub/Sub, Secret Manager)
- Hybrid (on-premise Kubernetes)

**Rules**:
- Same Helm chart MUST work for all providers
- Provider-specific config MUST be in values files
- Database URLs MUST be injected (not hardcoded)
- Secrets MUST use cloud provider stores
- Dapr MUST abstract pub/sub provider (Kafka ↔ Service Bus ↔ Pub/Sub)

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

**Forbidden in Spec-5 (Advanced Chat)**:
- Conversation deletion (only mark as archived)
- Message editing (only new corrections)
- Cross-user features (only within user context)
- External integrations (Slack, Discord, etc.)
- Voice/video chat
- File attachments or images
- Real-time sync across devices

**Forbidden in Spec-6 (Events)**:
- Event deletion or modification from event log
- Direct Kafka client usage (must use Dapr)
- Synchronous event processing (MUST NOT block requests)
- Custom message brokers (Kafka via Dapr only)
- Consumer rebalancing conflicts
- Event consumer stalling (monitoring required)

**Forbidden in Spec-7 (Cloud)**:
- Hardcoded environment-specific values in code
- Provider-specific container images (ECR, GCR, ACR in Helm)
- Schema migrations at deployment time (pre-deploy jobs required)
- Manual infrastructure setup (Helm chart MUST create all resources)
- Cross-provider resource mixing (e.g., AWS RDS + Azure Cosmos)
- Dual Kubernetes clusters (single cluster, multiple cloud possible via federation)

**Deferred to Future Specs**:
- Task sharing/collaboration
- Multi-user task boards
- Task comments or attachments
- Real-time updates
- Offline support
- Voice commands
- Image generation
- Custom agent personalities
- Advanced scheduling and automation
- Workflow orchestration
- AI-powered task recommendations

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

### Spec-5 Success Criteria (006-Advanced-Features)

Advanced chat features implementation is complete when:
- [ ] All new features are backward compatible
- [ ] Existing chat endpoints remain unchanged
- [ ] New features emit events for audit trail
- [ ] Feature flags control new functionality
- [ ] No schema changes to Conversation/Message tables
- [ ] Search/filtering works across user's conversations only
- [ ] Summaries are generated and stored in database
- [ ] Analytics metrics are exposed to Prometheus
- [ ] User PII is not logged or exposed
- [ ] All tests pass (existing + new)

### Spec-6 Success Criteria (007-Event-Architecture)

Event-driven architecture implementation is complete when:
- [ ] All state changes emit events to Kafka
- [ ] Events include all required fields (type, user_id, timestamp, data)
- [ ] Event schema is versioned and registered
- [ ] Kafka topics follow naming convention and versioning
- [ ] Dapr Pub/Sub is used for all event operations (not direct Kafka)
- [ ] Event consumers are idempotent and handle replays
- [ ] Local Kubernetes includes Kafka StatefulSet with persistence
- [ ] Event sourcing enables audit trail and replay
- [ ] Consumer lag is monitored and within SLA
- [ ] Helm chart includes Kafka subchart with values parameterization

### Spec-7 Success Criteria (008-Cloud-Deployment)

Cloud deployment implementation is complete when:
- [ ] Single Helm chart works on local K8s and all cloud providers
- [ ] Environment-specific values files control deployment differences
- [ ] Database is migrated to cloud-managed service (RDS/Azure DB/Cloud SQL)
- [ ] Secrets are stored in cloud provider vault (not .env file)
- [ ] Container images are pulled from cloud registry (parameterized)
- [ ] Ingress/load balancer is configured for cloud provider
- [ ] Dapr pub/sub is configured for cloud provider (MSK, Service Bus, Pub/Sub)
- [ ] Monitoring (Prometheus) and logging are sent to cloud provider
- [ ] Auto-scaling is configured (HPA based on CPU/memory)
- [ ] Rollback procedure is tested and documented
- [ ] All infrastructure created via Helm (no manual setup)

## Governance

### Amendment Process

1. Propose change with rationale
2. Document security and backward compatibility impact
3. Update version following semver:
   - MAJOR: Principle removal, redefinition, or phase lockdown
   - MINOR: New principle, expanded guidance, or phase extension
   - PATCH: Clarifications, typo fixes, non-semantic refinements
4. Update dependent templates if affected
5. Create PHR in `history/prompts/constitution/`
6. Commit with message: `docs: amend constitution to vX.Y.Z (<summary>)`

### Compliance Review

- All PRs MUST be verified against this constitution
- Authentication, Task Management (Spec-2), Frontend UI, Chat, and Event Architecture changes require explicit constitution check
- Phase-2 modifications require special justification and ADR
- Violations MUST be resolved before merge
- Security exceptions require documented justification and ADR
- Cloud deployment changes require approval from infrastructure team

### Supersession

This constitution supersedes all other authentication, task management, frontend UI,
chat, event architecture, and deployment guidance in the project. When conflicts arise,
this document takes precedence.

**Version**: 3.0.0 | **Ratified**: 2026-01-11 | **Last Amended**: 2026-03-15
