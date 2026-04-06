# Feature Specification: Advanced Todo Features & Event Architecture

**Feature Branch**: `006-advanced-features`
**Created**: 2026-03-15
**Status**: Draft
**Input**: Extend existing Todo system with priorities, tags, search, filters, due dates, reminders, recurring tasks, and event-driven architecture via Kafka

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Tasks with Priorities & Tags (Priority: P1)

As a todo user, I want to create tasks with priority levels and tags so that I can organize my work by importance and category.

**Why this priority**: Core feature that enables task organization. Without this, users cannot differentiate between urgent and routine work. Forms the foundation for filtering and sorting.

**Independent Test**: Can be fully tested by: (1) User creates task with High priority and "work" tag, (2) Backend stores both fields in database, (3) Task returned in API response with both fields. Delivers value by enabling basic task categorization.

**Acceptance Scenarios**:

1. **Given** user is logged in and on create task form, **When** user fills title, description, selects priority (High/Medium/Low), and adds tags, **Then** task is created with all fields and displays with correct priority badge and tags
2. **Given** a priority level is selected, **When** user saves the task, **Then** the priority is persisted in database
3. **Given** multiple tags are entered (comma-separated), **When** task is saved, **Then** all tags are stored and returned in subsequent GET requests
4. **Given** user omits priority and tags, **When** task is created, **Then** default priority (Medium) is assigned and tags list is empty
5. **Given** invalid priority value is provided, **When** user tries to save, **Then** validation error displays (e.g., "Priority must be Low, Medium, or High")

---

### User Story 2 - Search & Filter Tasks (Priority: P1)

As a todo user, I want to search tasks by title/description and filter by priority/tags so that I can quickly find specific tasks.

**Why this priority**: Enables users to manage large task lists efficiently. Search reduces cognitive load, filtering enables workflow optimization. Critical for usability as list grows.

**Independent Test**: Can be fully tested by: (1) User enters search term "groceries", (2) System returns only tasks with "groceries" in title/description, (3) User filters by priority=High, (4) Only high-priority tasks display. Delivers value by improving task discovery without requiring pagination.

**Acceptance Scenarios**:

1. **Given** user has 20 tasks with various titles, **When** user searches for "meeting", **Then** only tasks containing "meeting" in title or description display
2. **Given** tasks with different priorities exist, **When** user filters by priority=High, **Then** only High priority tasks display
3. **Given** tasks with multiple tags exist, **When** user filters by tag="work", **Then** only tasks with "work" tag display
4. **Given** both search and filters are applied, **When** user searches "email" and filters priority=Medium, **Then** system returns intersection (Medium priority tasks containing "email")
5. **Given** search returns no results, **When** user searches "nonexistent", **Then** empty state displays with message "No tasks match your search"
6. **Given** user applies filters, **When** user clicks reset/clear filters, **Then** all filters removed and full task list displays

---

### User Story 3 - Sort Tasks (Priority: P1)

As a todo user, I want to sort tasks by date, priority, or creation time so that I can organize my work according to urgency or timeline.

**Why this priority**: Sorting is essential for task prioritization workflows. P1 because it's part of core task management and enables users to focus on what matters most. Users expect sort functionality.

**Independent Test**: Can be fully tested by: (1) User opens task list, (2) User clicks sort by priority, (3) Tasks reorder with High→Medium→Low. Delivers value by enabling quick task prioritization.

**Acceptance Scenarios**:

1. **Given** tasks with different priorities, **When** user sorts by priority, **Then** tasks display High → Medium → Low
2. **Given** tasks with different due dates, **When** user sorts by due date (ascending), **Then** nearest due dates display first
3. **Given** user sorts by priority in descending order, **When** sort is applied, **Then** Low → Medium → High displays
4. **Given** multiple sort options available, **When** user selects sort by creation (newest first), **Then** most recent tasks display at top
5. **Given** tasks with no due date, **When** user sorts by due date, **Then** tasks without due date appear at end of list

---

### User Story 4 - Set Due Dates & Receive Reminders (Priority: P2)

As a todo user, I want to set due dates on tasks and receive reminders so that I don't miss important deadlines.

**Why this priority**: P2 because it's valuable for deadline management but system works without it. Improves user success for time-sensitive tasks. More complex to implement (background jobs).

**Independent Test**: Can be fully tested by: (1) User creates task with due date "2026-03-20", (2) System stores due date, (3) User sets reminder 1 hour before, (4) At reminder time, notification triggers. Delivers value by enabling deadline-driven workflows.

**Acceptance Scenarios**:

1. **Given** user creates a task, **When** user sets due date via date picker, **Then** due date is stored and displays on task card
2. **Given** task has a due date, **When** user sets reminder (1 hour before), **Then** reminder is scheduled and stored
3. **Given** reminder time approaches, **When** reminder triggers, **Then** user receives notification (in-app or email per setting)
4. **Given** task is overdue, **When** user views task list, **Then** overdue tasks display with red indicator/badge
5. **Given** task due date is today, **When** task displays, **Then** "Due Today" badge displays with appropriate color
6. **Given** user edits due date on existing task, **When** user saves, **Then** new due date is updated and any existing reminder is rescheduled

---

### User Story 5 - Create Recurring Tasks (Priority: P2)

As a todo user, I want to create recurring tasks so that I don't have to manually recreate tasks that repeat on a schedule.

**Why this priority**: P2 because valuable for productivity workflows but system is viable without it. Reduces user effort for routine tasks. Requires event-driven architecture.

**Independent Test**: Can be fully tested by: (1) User creates task marked "Recurring: Weekly", (2) System creates initial task, (3) After completion, next recurrence generates automatically. Delivers value by automating routine task creation.

**Acceptance Scenarios**:

1. **Given** user creates a task, **When** user marks "is_recurring: true" and selects pattern "Weekly", **Then** task is created and marked as recurring
2. **Given** recurring task exists, **When** recurrence is triggered, **Then** new task instance is created with same title/description/tags
3. **Given** recurring task is marked complete, **When** user completes it, **Then** original task stays in archive, new instance created automatically
4. **Given** user stops recurring task, **When** user toggles "is_recurring: false", **Then** no future recurrences are generated
5. **Given** recurring task has modifications (priority change), **When** new recurrence is generated, **Then** original settings preserved (new tasks inherit original pattern, not modifications)
6. **Given** recurring pattern is daily, **When** task completes, **Then** next instance generated within 24 hours

---

### User Story 6 - Event-Driven Task Operations (Priority: P2)

As a system operator, I want the backend to emit events for all task changes so that external services can react to task updates without direct coupling.

**Why this priority**: P2 because internal architecture feature. Necessary for scalability and audit trail. Enables future features (reminders, notifications, webhooks).

**Independent Test**: Can be fully tested by: (1) User creates task, (2) Backend publishes TaskCreated event to Kafka, (3) Event consumer receives event with correct task data. Delivers value by enabling loosely-coupled integrations.

**Acceptance Scenarios**:

1. **Given** user creates a task, **When** task is saved, **Then** TaskCreated event is published to task-events Kafka topic
2. **Given** user updates task priority, **When** update is persisted, **Then** TaskUpdated event is published with updated fields
3. **Given** user completes a task, **When** is_complete is toggled to true, **Then** TaskCompleted event is published
4. **Given** user deletes a task, **When** task is removed from database, **Then** TaskDeleted event is published
5. **Given** recurring task is triggered, **When** new task instance is created, **Then** TaskCreated event is published for new instance
6. **Given** event is published, **When** event contains all required fields (user_id, task_id, timestamp, action), **Then** event is valid per schema

---

### Edge Cases

- What happens when user creates task with due date in the past? (System should accept but flag as overdue)
- How does system handle recurring task if recurrence pattern is invalid? (Validation error, task not created)
- What if reminder time is set but due date is removed? (Reminder should be cleared automatically)
- How does system handle bulk tag creation vs. predefined tags? (Support both: existing tags reused, new tags created)
- What if user deletes a task that is recurring? (Entire series deleted or just this instance? → This instance only; mark original as non-recurring if user wishes to stop series)
- How does system handle task search when task title is empty? (Search returns all matching description; suggest improving UX)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extend the existing Task model with optional fields: `priority` (enum: Low/Medium/High, default: Medium), `tags` (list of strings), `due_date` (ISO-8601 datetime), `reminder_time` (ISO-8601 datetime), `is_recurring` (boolean), `recurring_pattern` (enum: Daily/Weekly/Monthly/null)

- **FR-002**: System MUST maintain backward compatibility with existing Task CRUD endpoints. All existing API contracts remain unchanged (no breaking changes to existing field names or response formats)

- **FR-003**: System MUST provide search capability: users can search tasks by title or description using text-based query. Search MUST be case-insensitive and support partial matches

- **FR-004**: System MUST provide filtering capability: users can filter tasks by priority and/or tags. Multiple tag filters MUST return tasks containing any of the selected tags (OR logic), while priority filter is single-select

- **FR-005**: System MUST provide sorting capability: users can sort tasks by priority (ascending: Low→Medium→High or descending), due date (ascending: soonest first or descending), or creation time

- **FR-006**: System MUST emit events to Kafka for all task state changes:
  - TaskCreated event when task is created (topic: task-events)
  - TaskUpdated event when task is modified (topic: task-events)
  - TaskCompleted event when is_complete flag is toggled (topic: task-events)
  - TaskDeleted event when task is deleted (topic: task-events)

- **FR-007**: System MUST support due date and reminder scheduling. When a task has a due_date, users MAY set a reminder_time. Reminders MUST trigger at scheduled time via background job

- **FR-008**: System MUST support recurring task creation. When is_recurring=true with a valid recurring_pattern, the system MUST automatically generate new task instances on the specified schedule

- **FR-009**: System MUST provide recurring task event stream. When a recurring task generates a new instance, a TaskCreated event is published (for audit trail)

- **FR-010**: System MUST enforce ownership rules for all new features. All queries MUST filter by authenticated user_id. New features MUST NOT expose cross-user data

- **FR-011**: System MUST NOT modify existing Task, User, or Conversation schemas. New data MUST be stored in extended Task table columns (not separate tables unless schema isolation required per constitution)

- **FR-012**: System MUST handle concurrent task updates safely. If task is updated while another request is processing, last-write-wins or optimistic locking (per existing pattern)

### Key Entities

- **Task** (extended): The existing task entity enriched with priority, tags, due dates, reminders, and recurrence info
  - Attributes (new): priority (Low/Medium/High), tags (list), due_date, reminder_time, is_recurring, recurring_pattern
  - Attributes (existing, preserved): id, user_id, title, description, is_complete, created_at, updated_at

- **TaskEvent**: Immutable record of a task state change published to Kafka
  - Attributes: event_type (TaskCreated/Updated/Completed/Deleted), user_id, task_id, timestamp, data (event-specific payload), version

- **Reminder**: Scheduled notification for a task
  - Attributes: id, user_id, task_id, reminder_time, status (pending/sent/expired), created_at

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create tasks with priorities and tags without API errors and data persists correctly (100% success rate for valid inputs)

- **SC-002**: Search functionality returns correct results within 500ms for typical task list (< 1000 tasks), with zero false negatives (all matching tasks returned)

- **SC-003**: Filter and sort operations complete within 200ms for typical task list, supporting combination of multiple filters and sorts simultaneously

- **SC-004**: Recurring tasks generate new instances at scheduled time (within 5-minute window of scheduled time) with 99.9% reliability

- **SC-005**: Reminders trigger at scheduled time (within 1-minute window) with 99% reliability

- **SC-006**: All task operations emit events to Kafka with zero data loss (every task mutation corresponds to exactly one event published)

- **SC-007**: Existing task endpoints remain fully backward compatible: all existing API clients continue to work without modification (100% API compatibility)

- **SC-008**: System supports task lists up to 50,000 tasks per user with search/filter/sort completing within 500ms

- **SC-009**: Event consumer lag does NOT exceed 5 minutes during normal operation, preventing stale notifications

- **SC-010**: New features do NOT introduce security vulnerabilities (all ownership rules enforced, cross-user access prevented, input validation on all new fields)

## Data Model Extensions

### Task Model (Extended)

```
Existing fields (PRESERVED):
- id: integer (PK)
- user_id: string (FK, index)
- title: string (max 255)
- description: string (nullable)
- is_complete: boolean (default false)
- created_at: datetime
- updated_at: datetime

New fields (ADDED):
- priority: enum (Low/Medium/High, default Medium)
- tags: JSON array of strings (default: [])
- due_date: datetime (nullable)
- reminder_time: datetime (nullable)
- is_recurring: boolean (default false)
- recurring_pattern: enum (Daily/Weekly/Monthly, nullable)
```

### Event Schema (Kafka)

All events follow this structure:

```json
{
  "event_type": "TaskCreated|TaskUpdated|TaskCompleted|TaskDeleted",
  "event_id": "uuid",
  "timestamp": "ISO-8601 datetime",
  "version": "1.0",
  "user_id": "string (authenticated user)",
  "task_id": "integer",
  "data": {
    // Event-specific fields
    "title": "string (for TaskCreated/Updated)",
    "priority": "enum",
    "tags": ["string"],
    "due_date": "datetime (nullable)",
    "is_recurring": "boolean",
    "is_complete": "boolean (for TaskCompleted)"
  }
}
```

## API Extensions

### Create Task (Extended)

**Endpoint**: `POST /api/{user_id}/tasks`

**Request Body** (all existing fields + new optional fields):

```json
{
  "title": "Submit Assignment",
  "description": "Complete project report",
  "priority": "High",
  "tags": ["work", "university"],
  "due_date": "2026-03-20T14:00:00Z",
  "reminder_time": "2026-03-20T13:00:00Z",
  "is_recurring": true,
  "recurring_pattern": "Weekly"
}
```

**Response**: Task with all fields (same as Task model extended)

**Backward Compatibility**: Existing clients that omit new fields continue to work (new fields optional with defaults)

### Search Tasks

**Endpoint**: `GET /api/{user_id}/tasks/search?q={query}`

**Query Parameters**:
- `q` (string): Text to search in title and description

**Response**: Array of matching tasks (filtered by user_id)

### Filter & Sort Tasks

**Endpoint**: `GET /api/{user_id}/tasks?priority={priority}&tags={tag1,tag2}&sort_by={field}&sort_order={asc|desc}`

**Query Parameters**:
- `priority` (optional): Low/Medium/High
- `tags` (optional): Comma-separated list of tags (OR logic)
- `sort_by` (optional): priority, due_date, created_at (default: created_at)
- `sort_order` (optional): asc or desc (default: desc)

**Response**: Filtered and sorted array of tasks

### Existing Endpoints (Unchanged)

All existing endpoints remain functional:
- `POST /api/{user_id}/tasks` (create) - accepts new optional fields
- `GET /api/{user_id}/tasks` (list) - returns extended task model
- `GET /api/{user_id}/tasks/{id}` (get) - returns extended task model
- `PUT /api/{user_id}/tasks/{id}` (update) - accepts new optional fields
- `DELETE /api/{user_id}/tasks/{id}` (delete)
- `PATCH /api/{user_id}/tasks/{id}/complete` (toggle) - unchanged

## Kafka Events

### Published Topics

1. **task-events** (required)
   - Purpose: Task lifecycle events (create, update, complete, delete)
   - Consumers: Audit service, recurring task service, analytics
   - Partitioning: By user_id for ordering guarantees per user

2. **reminders** (required)
   - Purpose: Reminder scheduling events
   - Consumers: Notification service (sends in-app or email)
   - Partitioning: By reminder_id for ordered processing

3. **task-updates** (optional, future)
   - Purpose: Real-time updates for connected clients
   - Consumers: WebSocket service (push updates to frontend)
   - Partitioning: By user_id

### Event Consumers (Services)

These services CONSUME events and react:

1. **Recurring Task Service**
   - Consumes: task-events (TaskCreated, TaskCompleted)
   - Action: When recurring task is completed, generate next instance
   - Publishes: TaskCreated event for new instance

2. **Notification Service**
   - Consumes: reminders topic
   - Action: Sends in-app or email notification to user
   - Integration: MUST NOT call task API directly (loose coupling)

3. **Audit Service** (optional, future)
   - Consumes: task-events (all)
   - Action: Stores complete event log for compliance
   - Integration: Append-only audit table

## Assumptions

1. **Kafka availability**: Kafka cluster is deployed and accessible by backend (deployed via Dapr per constitution)

2. **Priority defaults**: Tasks without explicit priority default to "Medium" (common SaaS pattern)

3. **Recurring task generation**: New instances are created at UTC midnight for daily patterns, specified day for weekly/monthly (user timezone handling deferred to Spec-007)

4. **Search behavior**: Search is case-insensitive, partial match only in title/description (not in tags; tag filter is exact match)

5. **Reminder precision**: Reminders trigger within 1-minute window (background job polling, not exact scheduling; streaming notifications Spec-007+)

6. **Event ordering**: Events are delivered in order per user_id (Kafka partitioning guarantee)

7. **Existing endpoint stability**: All existing Task API contracts remain 100% compatible (backward compatibility is non-negotiable per constitution)

8. **Database schema**: Extended Task table with new nullable columns (no separate tables to avoid schema fragmentation)

## Constraints & Non-Goals

### In Scope (This Spec)

- Task priorities (Low/Medium/High)
- Task tags (user-defined strings)
- Search by title/description
- Filter by priority and tags
- Sort by priority, due date, creation time
- Due dates and reminders
- Recurring tasks (Daily/Weekly/Monthly)
- Event publishing to Kafka
- Event consumers: Recurring Task Service, Notification Service
- Backward compatibility with existing Task API
- Ownership enforcement (same rules as Task CRUD)

### Out of Scope (Future Specs)

- Recurring task complexity: rrule syntax, exceptions, skipped dates → Spec-007+
- User timezone handling for due dates/reminders → Spec-007 (Cloud Deployment)
- Voice/image attachments on tasks → Future
- Task sharing/collaboration → Future
- Task workflows/state machines → Future
- Subtasks/hierarchies → Future
- Task templates → Future
- Advanced analytics/reporting → Future
- Mobile push notifications → Spec-007+
- Email notifications → Spec-007+ (integration with email service)
- Slack/Discord integrations → Future
- WebSocket real-time updates → Spec-007+ (requires Dapr pub/sub abstraction)

## Backward Compatibility

### Existing Clients (No Changes Required)

All existing API clients continue to work without modification:

1. **Existing create task call**:
   ```json
   POST /api/user123/tasks
   { "title": "Buy milk", "description": "2% milk" }
   ```
   → Still works. New fields optional with defaults.

2. **Existing list tasks call**:
   ```json
   GET /api/user123/tasks
   ```
   → Still returns tasks, now with additional priority/tags/due_date fields (safe to add fields in response)

3. **Existing update call**:
   ```json
   PUT /api/user123/tasks/42
   { "title": "Updated title" }
   ```
   → Still works. Can optionally include new fields.

### Breaking Changes: NONE

No breaking changes. All new features are additive.

## Testing Strategy

### Unit Tests (Backend)

- Task model validates priority enum
- Task model validates recurring_pattern enum
- Search query builder generates correct SQL
- Filter combiner applies filters correctly (AND for priority, OR for tags)
- Event publisher publishes correct event structure
- Reminder scheduler creates background jobs

### Integration Tests

- End-to-end: Create recurring task → verify new instance generated
- End-to-end: Set reminder → verify event published to reminders topic
- End-to-end: Search/filter combination → verify correct results
- Backward compatibility: Old API client → verify response includes new fields, client doesn't error

### Event Tests

- TaskCreated event published when task created
- TaskUpdated event published when task modified (not just any update, only field changes)
- TaskDeleted event published when task deleted
- Event schema validation: all required fields present

## Success Metrics

- **Adoption**: 50%+ of users create at least one task with priority/tags within 2 weeks
- **Search usage**: 30%+ of task list views include a search or filter
- **Reliability**: Zero event loss, 99% reminder delivery
- **Performance**: Search/filter/sort complete within 200ms for 50K task lists
- **Satisfaction**: Users rate task management features 4+ stars (post-launch survey)

