# Implementation Plan: Advanced Todo Features & Event Architecture

**Branch**: `006-advanced-features` | **Date**: 2026-03-15 | **Spec**: [Advanced Features & Event Architecture](./spec.md)

**Input**: Feature specification from `specs/006-advanced-features/spec.md`

---

## Summary

Extend the existing Task CRUD system with advanced features (priorities, tags, search, filtering, sorting, due dates, reminders, recurring tasks) while introducing event-driven architecture via Kafka. All changes are strictly additive with zero breaking changes to existing APIs. Implementation follows 7-phase approach: database extensions → API enhancements → search/filter/sort logic → reminder scheduling → recurring task automation → event publishing → event consumers.

---

## Technical Context

**Language/Version**: Python 3.11+ (existing backend)

**Primary Dependencies**:
- FastAPI (existing)
- SQLModel (existing)
- Neon PostgreSQL (existing)
- Apache Kafka (new)
- Dapr v1.10+ (new, for pub/sub abstraction)
- APScheduler (new, for reminder scheduling)
- APScheduler-Asyncio (new, for async scheduling)

**Storage**: Neon PostgreSQL (extend existing tables)

**Testing**: pytest (existing), add event integration tests

**Target Platform**: Linux server (FastAPI)

**Project Type**: Web application (backend focus for this phase)

**Performance Goals**:
- Search/filter/sort < 200ms for 50K tasks
- Recurring task generation within 5-minute window
- Reminder trigger within 1-minute window
- 99% uptime for event processing

**Constraints**:
- Zero breaking changes to existing Task API
- All new fields optional with sensible defaults
- Events must have zero data loss
- Consumer lag < 5 minutes

**Scale/Scope**:
- Support 50,000+ tasks per user
- 3 Kafka topics
- 3 event consumers (Recurring, Notification, Audit)
- 2 new API endpoints (search, filter/sort)

---

## Constitution Check

**Phase 1 Gates** (before implementation):

| Principle | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **VI** (Spec-Driven) | Spec approved before implementation | ✅ Pass | Spec-006 complete & quality-validated |
| **II** (Shared Secret) | BETTER_AUTH_SECRET consistency | ✅ Pass | Existing, no changes needed |
| **VII** (Task Ownership) | All queries filter by user_id | ✅ Pass | New features MUST enforce ownership |
| **VIII** (Task Persistence) | No in-memory storage | ✅ Pass | All data persisted in PostgreSQL |
| **XI** (Frontend Workspace) | Frontend work only in /frontend | ✅ Pass | Plan focuses on backend (Spec-006) |
| **XVI** (Phase-2 Lockdown) | No Task CRUD endpoint modifications | ✅ Pass | Existing endpoints preserved, new ones added |
| **XVII** (Stateless Chat) | No server-side session storage | ✅ Pass | Events stateless, consumers idempotent |
| **XXVI** (Event-Driven) | Async communication via events | ✅ Pass | All task ops emit events to Kafka |
| **XXVII** (Kafka Bus) | Use Kafka for message bus | ✅ Pass | task-events, reminders topics defined |
| **XXVIII** (Dapr Abstraction) | All pub/sub via Dapr (not direct Kafka) | ✅ Pass | Plan uses Dapr for abstraction |
| **XXX** (Message Versioning) | Event schema versioned | ✅ Pass | Event schema includes "version" field |
| **XXXV** (Advanced Chat) | Backward compatible | ✅ Pass | Zero breaking changes |

**Re-check gates**: After Phase 1 design, verify:
- Data model extensions don't break existing Task queries
- Event publishing doesn't delay API responses
- Search/filter/sort performance meets constraints

---

## Project Structure

### Documentation (this feature)

```text
specs/006-advanced-features/
├── spec.md                      # Feature specification (COMPLETE)
├── plan.md                      # This file (PHASE 0 OUTPUT)
├── research.md                  # Phase 0 research (PHASE 0 OUTPUT)
├── data-model.md                # Phase 1 design (PHASE 1 OUTPUT)
├── contracts/                   # Phase 1 API contracts (PHASE 1 OUTPUT)
│   ├── search-api.md
│   ├── filter-sort-api.md
│   └── events-schema.md
├── quickstart.md                # Phase 1 developer guide (PHASE 1 OUTPUT)
├── checklists/
│   └── requirements.md          # Quality checklist (COMPLETE)
└── tasks.md                     # Phase 2 task breakdown (NOT created by /sp.plan)
```

### Source Code (Backend)

```text
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── tasks.py         # EXISTING - extend with search/filter/sort
│   │   │   ├── events.py        # NEW - event publishing routes
│   │   │   └── reminders.py     # NEW - reminder scheduling routes
│   │   ├── mcp_server/          # EXISTING
│   │   │   └── tools.py         # Extend with new task query tools
│   │   └── deps.py              # EXISTING
│   ├── models/
│   │   ├── task.py              # EXISTING - extend with new fields
│   │   └── event.py             # NEW - EventLog model
│   ├── schemas/
│   │   ├── task.py              # EXISTING - extend with new fields
│   │   └── event.py             # NEW - EventRequest, EventResponse schemas
│   ├── services/
│   │   ├── task_service.py      # EXISTING - extend with search/filter/sort
│   │   ├── event_service.py     # NEW - event publishing service
│   │   ├── reminder_service.py  # NEW - reminder scheduling service
│   │   └── recurring_service.py # NEW - recurring task automation
│   ├── workers/                 # NEW - background job consumers
│   │   ├── __init__.py
│   │   ├── recurring_worker.py  # Consumes task-events, generates recurrences
│   │   ├── reminder_worker.py   # Consumes reminders, triggers notifications
│   │   └── audit_worker.py      # Consumes task-events, stores audit log
│   ├── config.py                # EXISTING - add Kafka/Dapr config
│   ├── database.py              # EXISTING - add migration
│   └── main.py                  # EXISTING - register new routes
├── migrations/                  # NEW - database migrations
│   └── alembic/
│       ├── versions/
│       │   └── 001_extend_task_model.py # Add new columns to tasks table
│       └── env.py
├── tests/
│   ├── unit/
│   │   ├── test_task_search.py         # NEW
│   │   ├── test_task_filter_sort.py    # NEW
│   │   ├── test_reminders.py           # NEW
│   │   └── test_recurring.py           # NEW
│   ├── integration/
│   │   ├── test_event_publishing.py    # NEW
│   │   ├── test_event_consumers.py     # NEW
│   │   └── test_task_with_events.py    # NEW
│   └── contract/
│       ├── test_search_api.py          # NEW
│       └── test_filter_sort_api.py     # NEW
└── requirements.txt             # EXISTING - add Kafka, APScheduler, Dapr

# Frontend (minimal for Spec-006 backend focus)
frontend/
├── app/
│   └── (protected)/
│       └── dashboard/
│           └── page.tsx         # EXISTING - update to show new fields
└── components/
    ├── tasks/
    │   ├── TaskCard.tsx         # EXISTING - show priority badge, tags, due date
    │   ├── TaskForm.tsx         # EXISTING - add priority, tags, due date fields
    │   ├── SearchBar.tsx        # NEW - search component
    │   └── FilterSort.tsx       # NEW - filter and sort controls
    └── ui/
        └── (existing UI components)

# Kubernetes / Helm
todo-chatbot/
├── templates/
│   ├── backend-deployment.yaml         # EXISTING - add Kafka env vars
│   ├── kafka-statefulset.yaml          # NEW - Kafka in local K8s
│   ├── dapr-config.yaml                # NEW - Dapr pub/sub config
│   └── recurring-worker-deployment.yaml # NEW - recurring task consumer
│       reminder-worker-deployment.yaml  # NEW - reminder consumer
│       audit-worker-deployment.yaml     # NEW - audit consumer
├── values.yaml                         # EXISTING - add Kafka/Dapr config
└── values-local.yaml                   # NEW - local K8s overrides
```

**Structure Decision**: Web application with backend focus. Existing backend extended with event-driven components. Frontend minimal updates to display new fields. Kubernetes deployments for local + cloud.

---

## Implementation Phases

### Phase 0: Research & Clarification (OUTPUT: research.md)

**Decisions to finalize:**

1. **Database Migration Strategy**
   - ❓ Use Alembic for migrations or plain SQL?
   - ❓ Zero-downtime migration strategy for existing tasks?
   - ❓ Default values for existing rows (priority=Medium, tags=[])?
   - **Decision**: Use Alembic (standard SQLModel pattern), add defaults to migration script

2. **Kafka Implementation Pattern**
   - ❓ Direct Kafka client or Dapr Pub/Sub?
   - ❓ Event serialization format (JSON vs Avro)?
   - ❓ Schema registry integration?
   - **Decision**: Dapr Pub/Sub (per constitution XXVIII), JSON events with version field, optional schema registry

3. **Search Implementation**
   - ❓ Full-text search in PostgreSQL or separate search service?
   - ❓ Indexing strategy for performance?
   - ❓ Wildcard search (LIKE) acceptable or need better pattern?
   - **Decision**: PostgreSQL full-text search (ilike) with GIN index, acceptable for MVP

4. **Reminder Scheduling**
   - ❓ APScheduler background jobs or external service?
   - ❓ How to handle reschedules if due date changes?
   - ❓ Timezone handling for reminders?
   - **Decision**: APScheduler with async support, reschedule on due date change, UTC only (timezone handling → Spec-007)

5. **Recurring Task Generation**
   - ❓ Scheduled job vs event-driven from completion?
   - ❓ Where to store next_recurrence_date?
   - ❓ How to handle user edits to recurring task settings?
   - **Decision**: Event-driven on TaskCompleted, calculate next date in memory, preserve original task settings

6. **Event Consumer Deployment**
   - ❓ Single process with multiple consumers or separate services?
   - ❓ How to handle consumer failure/retry?
   - ❓ Offset management strategy?
   - **Decision**: Separate consumer services (Kubernetes deployments), Dapr handles retry/offset

### Phase 1: Design & Contracts (OUTPUT: data-model.md, contracts/*, quickstart.md)

#### Phase 1.1: Data Model Design

**Extend Task Model** (SQLModel):

```
Existing fields (PRESERVED):
├── id: int (PK)
├── user_id: str (FK, index)
├── title: str (max 255)
├── description: str (nullable)
├── is_complete: bool (default False)
├── created_at: datetime
└── updated_at: datetime

New fields (ADDED - all optional/nullable):
├── priority: str (enum: Low/Medium/High, default: Medium)
├── tags: JSON array (default: [])
├── due_date: datetime (nullable)
├── reminder_time: datetime (nullable)
├── is_recurring: bool (default: False)
└── recurring_pattern: str (enum: Daily/Weekly/Monthly, nullable)

Indexes (for performance):
├── (user_id, priority) - for filtering
├── (user_id, tags) - for tag filtering
├── (user_id, due_date) - for sorting
├── (user_id, created_at) - for sorting
└── (user_id, title) GIN - for full-text search
```

**New Models**:

1. **EventLog** (SQLModel) - Immutable audit trail
   ```
   id: int (PK)
   user_id: str (FK, index)
   task_id: int (FK)
   event_type: str (TaskCreated/Updated/Completed/Deleted)
   data: JSON (complete event payload)
   timestamp: datetime (index)
   version: int
   ```

2. **Reminder** (SQLModel) - Scheduled notifications
   ```
   id: int (PK)
   user_id: str (FK, index)
   task_id: int (FK)
   reminder_time: datetime (index)
   status: str (Pending/Sent/Expired)
   created_at: datetime
   updated_at: datetime
   ```

#### Phase 1.2: API Contract Design

**Modified Endpoints** (Backward Compatible):

1. **POST /api/{user_id}/tasks** (Create)
   - Request: Add optional fields (priority, tags, due_date, reminder_time, is_recurring, recurring_pattern)
   - Response: Task with all fields
   - Backward Compatible: Existing clients without new fields still work

2. **PUT /api/{user_id}/tasks/{id}** (Update)
   - Request: Add optional fields for updates
   - Response: Updated task with all fields
   - Special: If due_date changes, reschedule reminder

3. **PATCH /api/{user_id}/tasks/{id}/complete** (Toggle)
   - Existing behavior preserved
   - New: If recurring task, generate new instance on completion

**New Endpoints**:

1. **GET /api/{user_id}/tasks/search?q={query}**
   - Query: q (string, required)
   - Response: Task[] (matching tasks)
   - Performance: < 200ms for 50K tasks

2. **GET /api/{user_id}/tasks?priority={p}&tags={t}&sort_by={field}&sort_order={asc|desc}**
   - Filters: priority, tags (both optional)
   - Sort: by priority, due_date, created_at
   - Performance: < 200ms for 50K tasks

#### Phase 1.3: Event Schema

**Kafka Events** (JSON):

```json
{
  "event_type": "TaskCreated|TaskUpdated|TaskCompleted|TaskDeleted",
  "event_id": "uuid",
  "timestamp": "ISO-8601",
  "version": "1.0",
  "user_id": "string",
  "task_id": "integer",
  "data": {
    "title": "string",
    "priority": "enum",
    "tags": ["string"],
    "due_date": "ISO-8601 or null",
    "is_recurring": "boolean",
    "recurring_pattern": "enum or null",
    "is_complete": "boolean"
  }
}
```

### Phase 2: Detailed Implementation Phases

#### Phase 2.1: Database Model Updates

**Files to Modify**:
1. `backend/app/models/task.py` - Add new fields
2. `backend/app/schemas/task.py` - Add validators, extend schemas
3. `backend/app/database.py` - Update init_db()
4. `backend/migrations/alembic/versions/001_*.py` - Create migration

**Deliverables**:
- SQLModel extended with 6 new fields
- Alembic migration script
- Validation rules for priority, pattern enums
- Indexes created for performance

**Testing**:
- Unit: Field validation (priority enum, tag format)
- Integration: Migration runs without errors, existing tasks unaffected

---

#### Phase 2.2: API Extensions (CRUD + Events)

**Files to Create**:
- `backend/app/services/event_service.py` - Event publishing
- `backend/app/api/routes/events.py` - Event endpoints (internal monitoring)
- `backend/app/schemas/event.py` - Event schemas

**Files to Modify**:
- `backend/app/api/routes/tasks.py` - Emit events on CRUD
- `backend/app/services/task_service.py` - Emit events in service layer
- `backend/app/main.py` - Register new routes
- `backend/app/config.py` - Add Kafka/Dapr config

**Deliverables**:
- Event publishing on TaskCreated, TaskUpdated, TaskCompleted, TaskDeleted
- Event schema validation
- EventLog table populated on each mutation
- Zero breaking changes to existing endpoints

**Testing**:
- Unit: Event schema valid, fields populated
- Integration: Create task → event published to Kafka
- Contract: Existing clients still work

---

#### Phase 2.3: Search/Filter/Sort Logic

**Files to Create**:
- `backend/app/services/query_service.py` - Search/filter/sort builders

**Files to Modify**:
- `backend/app/api/routes/tasks.py` - Add search, filter, sort endpoints
- `backend/app/services/task_service.py` - Add search/filter/sort methods

**Deliverables**:
- Full-text search on title/description
- Filter by priority and tags (OR logic)
- Sort by priority, due_date, created_at
- Query combination (search + filters + sort simultaneously)
- GIN indexes for performance

**Testing**:
- Unit: Query builders generate correct SQL
- Integration: Search returns matching tasks, filters work
- Performance: < 200ms for 50K tasks

---

#### Phase 2.4: Reminder Scheduling

**Files to Create**:
- `backend/app/services/reminder_service.py` - Reminder scheduling via APScheduler

**Files to Modify**:
- `backend/app/api/routes/tasks.py` - Allow reminder_time in request
- `backend/app/services/task_service.py` - Create/reschedule reminders
- `backend/app/main.py` - Start APScheduler on app startup

**Models**:
- Create Reminder model (task_id, user_id, reminder_time, status)

**Deliverables**:
- Reminders stored in database
- APScheduler jobs scheduled at reminder_time
- On due_date change, reschedule existing reminder
- Notify user when reminder triggers (Spec-7+ integration point)

**Testing**:
- Unit: Reminder calculates correct trigger time
- Integration: Set reminder → scheduled job created

---

#### Phase 2.5: Recurring Task Automation

**Files to Create**:
- `backend/app/services/recurring_service.py` - Recurrence logic

**Files to Modify**:
- `backend/app/api/routes/tasks.py` - Allow is_recurring, recurring_pattern in request
- `backend/app/services/task_service.py` - Generate next instance
- `backend/app/services/event_service.py` - Consume TaskCompleted events

**Deliverables**:
- TaskCompleted events trigger next instance generation
- New instance inherits original title, description, tags, priority, pattern
- Original task archived (is_complete=true preserved)
- Can toggle is_recurring to stop

**Testing**:
- Unit: Next date calculation for Daily/Weekly/Monthly
- Integration: Complete recurring task → new instance generated within 5 minutes

---

#### Phase 2.6: Kafka Event Publishing

**Files to Create**:
- `backend/app/workers/__init__.py` - Worker base classes
- `backend/app/workers/event_producer.py` - Event publishing via Dapr

**Files to Modify**:
- `backend/app/services/event_service.py` - Publish to Kafka via Dapr
- `backend/app/config.py` - Add Dapr endpoint config
- `backend/requirements.txt` - Add dapr-client
- `todo-chatbot/templates/dapr-config.yaml` - NEW
- `todo-chatbot/templates/backend-deployment.yaml` - Add Dapr sidecar

**Deliverables**:
- All task mutations publish events to Kafka
- Zero data loss (guaranteed at-least-once delivery)
- Event consumer offset tracking
- Dapr pub/sub abstraction (provider-agnostic)

**Testing**:
- Integration: Create task → event on Kafka topic
- Consumer: Event consumed successfully

---

#### Phase 2.7: Event Consumer Services

**Files to Create**:
- `backend/app/workers/recurring_worker.py` - Recurring task generator
- `backend/app/workers/reminder_worker.py` - Reminder trigger (Spec-7+)
- `backend/app/workers/audit_worker.py` - Audit log populator

**Deployment**:
- `todo-chatbot/templates/recurring-worker-deployment.yaml` - K8s deployment
- `todo-chatbot/templates/reminder-worker-deployment.yaml` - K8s deployment
- `todo-chatbot/templates/audit-worker-deployment.yaml` - K8s deployment

**Deliverables**:
- Recurring Task Service: Consumes task-events, generates new instances
- Notification Service: Consumes reminders, triggers notifications (stub → Spec-7)
- Audit Service: Consumes task-events, populates audit log

**Testing**:
- Integration: Event consumed, action taken (new task created, notification sent, etc.)
- Consumer lag: < 5 minutes

---

## Files to Modify Summary

### Backend Core

| File | Change | Priority |
|------|--------|----------|
| `backend/app/models/task.py` | Extend with 6 new fields | P1 |
| `backend/app/schemas/task.py` | Add validators, extend schemas | P1 |
| `backend/app/services/task_service.py` | Add search/filter/sort, emit events, recurring logic | P1 |
| `backend/app/api/routes/tasks.py` | Add search/filter/sort endpoints, emit events | P1 |
| `backend/app/config.py` | Add Kafka, Dapr, APScheduler config | P1 |
| `backend/app/database.py` | Update init_db() for migrations | P1 |
| `backend/app/main.py` | Register new routes, start schedulers | P1 |
| `backend/requirements.txt` | Add Kafka, APScheduler, Dapr dependencies | P1 |

### New Backend Services

| File | Purpose | Priority |
|------|---------|----------|
| `backend/app/services/event_service.py` | Event publishing via Dapr | P1 |
| `backend/app/services/reminder_service.py` | Reminder scheduling | P2 |
| `backend/app/services/recurring_service.py` | Recurring task generation | P2 |
| `backend/app/workers/recurring_worker.py` | Recurring task consumer | P2 |
| `backend/app/workers/reminder_worker.py` | Reminder consumer | P2 |
| `backend/app/workers/audit_worker.py` | Audit log consumer | P3 |

### Database Migrations

| File | Purpose | Priority |
|------|---------|----------|
| `backend/migrations/alembic/versions/001_*.py` | Add columns to tasks table | P1 |

### Frontend Minimal Updates

| File | Change | Priority |
|------|--------|----------|
| `frontend/components/tasks/TaskCard.tsx` | Display priority badge, tags, due date | P1 |
| `frontend/components/tasks/TaskForm.tsx` | Add priority, tags, due date inputs | P1 |
| `frontend/components/tasks/SearchBar.tsx` | NEW - search component | P2 |
| `frontend/components/tasks/FilterSort.tsx` | NEW - filter and sort controls | P2 |

### Kubernetes / Helm

| File | Change | Priority |
|------|--------|----------|
| `todo-chatbot/templates/backend-deployment.yaml` | Add Kafka env vars, Dapr sidecar | P1 |
| `todo-chatbot/templates/dapr-config.yaml` | NEW - Dapr pub/sub config | P1 |
| `todo-chatbot/templates/kafka-statefulset.yaml` | NEW - Kafka in local K8s | P1 |
| `todo-chatbot/templates/recurring-worker-deployment.yaml` | NEW - recurring task consumer | P2 |
| `todo-chatbot/templates/reminder-worker-deployment.yaml` | NEW - reminder consumer | P2 |
| `todo-chatbot/templates/audit-worker-deployment.yaml` | NEW - audit consumer | P3 |
| `todo-chatbot/values.yaml` | Add Kafka/Dapr config | P1 |
| `todo-chatbot/values-local.yaml` | NEW - local K8s overrides | P1 |

---

## Critical Implementation Notes

### 1. Database Migrations (Zero Downtime)

All new Task fields are NULLABLE with sensible defaults:
```sql
ALTER TABLE tasks ADD COLUMN priority VARCHAR(20) DEFAULT 'Medium';
ALTER TABLE tasks ADD COLUMN tags JSON DEFAULT '[]';
ALTER TABLE tasks ADD COLUMN due_date TIMESTAMP NULL;
ALTER TABLE tasks ADD COLUMN reminder_time TIMESTAMP NULL;
ALTER TABLE tasks ADD COLUMN is_recurring BOOLEAN DEFAULT FALSE;
ALTER TABLE tasks ADD COLUMN recurring_pattern VARCHAR(20) NULL;
```

This allows:
- Existing tasks continue to work with defaults
- No downtime for existing API clients
- Gradual rollout of new features

### 2. Event Publishing Integration

Events published SYNCHRONOUSLY in task_service, NOT blocking API response:
```python
# In task_service.create_task():
task = db.add(task)
db.commit()  # Task committed
event_service.publish_event(...)  # Async event publishing (via Dapr)
return task  # Immediate response
```

This ensures:
- API responses not blocked by Kafka
- At-least-once delivery (Dapr handles retries)
- Consumer lag acceptable (< 5 minutes)

### 3. Recurring Task Generation

Triggered on TaskCompleted event (not scheduled job):
```
User completes task
  ↓
TaskCompleted event published
  ↓
Recurring Task Service consumes event
  ↓
If is_recurring=true, calculate next_date
  ↓
Create new Task with next_date as due_date
  ↓
Publish TaskCreated event for audit trail
```

This ensures:
- Recurrences tied to user action (completion)
- No orphaned tasks from failed schedules
- Full audit trail via events

### 4. Search Performance

Use PostgreSQL full-text search with GIN indexes:
```sql
CREATE INDEX idx_tasks_search ON tasks USING GIN(
  to_tsvector('english', title || ' ' || COALESCE(description, ''))
) WHERE user_id = ?;
```

This ensures:
- < 200ms search for 50K tasks
- Built-in PostgreSQL functionality (no external search service)
- Works with existing Neon PostgreSQL

### 5. Ownership Enforcement

All new queries MUST filter by authenticated user_id:
```python
# Search
query = select(Task).where(
    Task.user_id == user_id,
    to_tsvector('english', ...).match('websearch_to_tsquery(...)')
)

# Filter
query = select(Task).where(
    Task.user_id == user_id,
    Task.priority == priority,
    Task.tags.contains(tag)
)
```

This ensures:
- No cross-user data leakage
- Compliance with Constitution Principle VII

### 6. Event Consumer Idempotency

All consumers MUST be idempotent (safe to replay):
```python
# Recurring Worker
def consume_task_completed(event):
    task = db.get(Task, event.task_id, event.user_id)
    if task.is_recurring:
        next_task = db.get_or_create(
            Task.user_id == event.user_id AND Task.id == event.task_id + "_next"
        )
        if not next_task.exists():  # Only create if not exists
            next_task.create()
```

This ensures:
- Safe message replay (Kafka guarantees)
- No duplicate recurrences
- Consumer lag tolerance

---

## Testing Strategy

### Unit Tests
- Task model validation (enums, formats)
- Search query builders
- Filter/sort logic
- Event schema validation
- Reminder date calculations
- Recurring date calculations

### Integration Tests
- Create task → event published
- Event consumed → action taken (recurrence generated, etc.)
- Search returns correct results
- Filter/sort combinations work
- Reminder triggers at scheduled time
- Recurring task generates instance

### Contract Tests
- Existing API clients still work
- Search endpoint response format correct
- Filter/sort endpoint parameters validated

### End-to-End Tests
- Complete recurring task → new instance auto-generated
- Set reminder → notification triggered (Spec-7)
- Search/filter/sort from UI → correct results displayed

---

## Dependencies & External Services

| Service | Purpose | Implementation |
|---------|---------|-----------------|
| **Kafka** | Event bus | Docker + StatefulSet in Kubernetes |
| **Dapr** | Pub/Sub abstraction | Kubernetes sidecar injection |
| **PostgreSQL** | Task storage | Existing Neon (no changes) |
| **APScheduler** | Reminder scheduling | Python library (async) |

---

## Success Metrics

| Metric | Target | Validation |
|--------|--------|-----------|
| API backward compatibility | 100% | Old clients work without changes |
| Search performance | < 200ms (50K tasks) | Load test |
| Filter/sort performance | < 200ms | Load test |
| Event loss | 0 (zero data loss) | Monitor Kafka offset lag |
| Recurring generation delay | 5 minutes | Monitor consumer lag |
| Reminder trigger accuracy | ±1 minute | Test with sample reminders |

---

## Phase Breakdown & Deliverables

| Phase | Focus | Deliverables | Timing |
|-------|-------|--------------|--------|
| **Phase 0** | Research | research.md | 1-2 days |
| **Phase 1** | Design | data-model.md, contracts/, quickstart.md | 2-3 days |
| **Phase 1.1** | Data model | Extended Task schema, migration | 1 day |
| **Phase 1.2** | API design | API contracts, response schemas | 1 day |
| **Phase 1.3** | Event schema | Event structure, Kafka topics | 1 day |
| **Phase 2.1** | DB updates | Migration script, indexes | 1 day |
| **Phase 2.2** | API + events | Event publishing, backward compat | 2 days |
| **Phase 2.3** | Search/filter/sort | Query builders, new endpoints | 2 days |
| **Phase 2.4** | Reminders | APScheduler integration | 1 day |
| **Phase 2.5** | Recurring | Recurrence logic, generation | 1 day |
| **Phase 2.6** | Kafka integration | Dapr pub/sub, producers | 2 days |
| **Phase 2.7** | Consumers | Worker services, deployments | 2 days |
| **Testing** | QA | Unit/integration/E2E tests | 3 days |

**Total Estimated**: 3-4 weeks (2 designers, 2-3 engineers)

---

## Risk Mitigation

| Risk | Mitigation | Owner |
|------|-----------|-------|
| Breaking existing API | All new fields optional with defaults | Backend Lead |
| Event loss | Dapr at-least-once delivery, monitoring | Infrastructure |
| Consumer lag exceeds SLA | Consumer scaling, monitoring | Infrastructure |
| Search performance | GIN indexing, load testing | Backend |
| Recurring task generation delay | Event-driven (not scheduled), monitoring | Backend |
| Database migration failure | Test on staging, rollback procedure | DBA |

---

## Go/No-Go Criteria

✅ **GO** if:
- [ ] Constitution Check: All gates pass
- [ ] Specification approved by product
- [ ] Database migration tested on staging
- [ ] Event schema approved by platform team
- [ ] Performance benchmarks meet targets (search < 200ms, etc.)

❌ **NO-GO** if:
- [ ] Breaking changes to existing API
- [ ] Event loss risk (> 0.1%)
- [ ] Search performance > 500ms
- [ ] Consumer lag > 5 minutes
- [ ] Security vulnerabilities (cross-user access, etc.)

