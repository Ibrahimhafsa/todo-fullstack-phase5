# Tasks: AI Chatbot with MCP Tools & Agent Backend (Spec-4)

**Input**: Design documents from `specs/004-ai-chatbot/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md (Phase 0), data-model.md (Phase 1), contracts/ (Phase 1)

**Organization**: Tasks are grouped by user story (US1-US4) to enable independent implementation and testing of each story.

**Format**: `[ID] [P?] [Story] Description with exact file paths`
- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- File paths: All absolute or relative from repository root (`backend/app/...`)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and shared layer setup

**Do NOT modify Phase-2 code during these tasks**

- [ ] T001 Update requirements.txt with openai-agents and mcp SDKs in `backend/requirements.txt`
- [ ] T002 [P] Create `.env.example` with OPENAI_API_KEY, OPENAI_MODEL, CHAT_RATE_LIMIT in `backend/.env.example`
- [ ] T003 [P] Create MCP Server directory structure: `backend/app/api/mcp_server/__init__.py`, `tools.py`, `server.py`
- [ ] T004 [P] Create chat service directory and stubs: `backend/app/services/chat_service.py` (empty class)
- [ ] T005 [P] Create chat routes directory and stubs: `backend/app/api/routes/chat.py` (empty router)
- [ ] T006 Create conversation models file: `backend/app/models/conversation.py` (will add Conversation/Message models in Phase 2)

**Acceptance Criteria**:
- ✅ requirements.txt contains `openai-agents` and `mcp`
- ✅ All new directories created and stubs in place
- ✅ Phase-2 files (tasks.py, user.py, task_service.py) UNTOUCHED
- ✅ No imports yet (avoid circular dependencies)

---

## Phase 2: Foundational (Blocking Prerequisites for All User Stories)

**Purpose**: Core infrastructure that MUST complete before ANY user story can proceed

**⚠️ CRITICAL**: Phase-2 task CRUD endpoints remain untouched during these tasks

### 2A: Database Models & Configuration

- [ ] T007 Create Conversation SQLModel in `backend/app/models/conversation.py`: fields {id (PK), user_id (indexed), title, created_at, updated_at}
- [ ] T008 Create Message SQLModel in `backend/app/models/conversation.py`: fields {id (PK), conversation_id (FK), user_id (indexed), role, content, created_at} with composite index on (user_id, created_at)
- [ ] T009 [P] Update `backend/app/config.py` to add OPENAI_API_KEY, OPENAI_MODEL (default: gpt-4), CHAT_RATE_LIMIT (default: 20) from environment variables
- [ ] T010 Update `backend/app/database.py` to auto-create Conversation and Message tables on app startup (use existing SQLModel pattern from Phase-2)

**Acceptance Criteria**:
- ✅ Conversation and Message models properly defined with all fields
- ✅ Indexes created correctly
- ✅ Config loads OpenAI settings from environment
- ✅ Tables created on startup (pytest `test_database_init()`)
- ✅ Phase-2 Task/User tables UNCHANGED

### 2B: MCP Tool Foundation (Wraps Existing Phase-2 Logic)

**CRITICAL RULE**: MCP tools ONLY call existing Phase-2 task_service methods. NO new task logic.

- [ ] T011 Implement MCP tool definitions in `backend/app/api/mcp_server/tools.py`: stub for 6 tools (list_tasks, get_task, create_task, update_task, delete_task, complete_task) with proper function signatures
- [ ] T012 [P] Each MCP tool wrapper: call corresponding task_service method directly (import task_service, verify method exists)
  - list_tasks(user_id) → task_service.list_tasks(session, user_id)
  - get_task(user_id, task_id) → task_service.get_task(session, user_id, task_id)
  - create_task(user_id, title, description) → task_service.create_task(session, user_id, TaskCreate(...))
  - update_task(user_id, task_id, title, description) → task_service.update_task(session, user_id, task_id, TaskUpdate(...))
  - delete_task(user_id, task_id) → task_service.delete_task(session, user_id, task_id)
  - complete_task(user_id, task_id) → task_service.toggle_complete(session, user_id, task_id)
- [ ] T013 Implement MCP Server initialization in `backend/app/api/mcp_server/server.py`: instantiate MCP Server and register 6 tools
- [ ] T014 [P] Add unit tests for MCP tools: `backend/tests/unit/test_mcp_tools.py` verifying each tool calls correct task_service method with correct params

**Acceptance Criteria**:
- ✅ 6 MCP tools defined and registered with MCP Server
- ✅ Each tool calls corresponding Phase-2 task_service method
- ✅ NO task_service methods modified or duplicated
- ✅ Unit tests verify tool wrapping (mock task_service)
- ✅ Tool errors properly wrapped for MCP compatibility

### 2C: Rate Limiting & Configuration

- [ ] T015 Implement per-user rate limiting in `backend/app/services/chat_service.py`: RateLimiter class tracking requests per user per minute
- [ ] T016 [P] Add rate limiting unit tests in `backend/tests/unit/test_chat_service.py`: verify counter increments, resets on minute boundary, raises error after limit
- [ ] T017 Create chat service stub methods: store_user_message(), store_assistant_message(), get_conversation_history() (empty implementations)

**Acceptance Criteria**:
- ✅ Rate limiter tracks per user (from JWT user_id)
- ✅ Limit: 20 requests/minute (configurable)
- ✅ Returns 429 when exceeded
- ✅ Counter resets at minute boundary
- ✅ Unit tests pass

**Checkpoint**: Foundation complete - all user story work can now begin in parallel

---

## Phase 3: User Story 1 - Ask AI to Help Manage Tasks (Priority: P1) 🎯 MVP

**Goal**: Enable users to send natural language messages to AI, which processes them via MCP tools and returns responses. Core chat functionality.

**Independent Test**:
1. Authenticated user sends POST to `/api/{user_id}/chat` with message "Create a task called 'Buy groceries'"
2. AI agent calls create_task MCP tool
3. Task created in database via Phase-2 endpoint
4. Response stored in Message table
5. Response returned to user with message ID and timestamp

### 3A: Chat Service Implementation

- [ ] T018 [US1] Implement chat_service.send_message(user_id, conversation_id, message_text) in `backend/app/services/chat_service.py`:
  - Accept message from user
  - Retrieve conversation history (or create new conversation if conversation_id is None)
  - Initialize OpenAI Agents with MCP tools
  - Pass message + history to agent
  - Receive agent response
  - Store user message in Message table (role='user')
  - Store agent response in Message table (role='assistant')
  - Return response object {message_id, role, content, timestamp}
  - Return 503 if OpenAI API unreachable

**Acceptance Criteria**:
- ✅ Message storage works (verified by database query)
- ✅ OpenAI Agents called with correct context
- ✅ Agent response stored
- ✅ User can see full response
- ✅ Error handling: OpenAI timeout → retry 3x with backoff → return 503

### 3B: Chat Endpoint Implementation

- [ ] T019 [US1] Implement POST `/api/{user_id}/chat` endpoint in `backend/app/api/routes/chat.py`:
  - Extract JWT, get user_id from claims
  - Verify path {user_id} matches JWT user_id (return 401 if not)
  - Parse request body: {conversation_id (optional), message}
  - Call chat_service.send_message()
  - Return {message_id, role, content, timestamp, conversation_id}
  - Handle errors: 400 (validation), 401 (auth), 429 (rate limit), 503 (OpenAI)

- [ ] T020 [US1] Register chat router in `backend/app/main.py`: include routes from chat.py in FastAPI app

**Acceptance Criteria**:
- ✅ Endpoint accepts POST with JWT
- ✅ User_id extracted from JWT (not path)
- ✅ Message stored and processed
- ✅ Response returned in < 30 seconds (p95)
- ✅ Error responses include `detail` field
- ✅ No Phase-2 task endpoint modified

### 3C: Integration Tests for US1

- [ ] T021 [P] [US1] Integration test: E2E chat flow in `backend/tests/integration/test_chat_endpoint.py`
  - Create authenticated user (JWT)
  - Send POST to /api/{user_id}/chat with "Create a task"
  - Verify response received
  - Verify Message table has user + assistant entries
  - Verify task created in Task table

- [ ] T022 [P] [US1] Integration test: MCP tool integration in `backend/tests/integration/test_mcp_task_integration.py`
  - Mock OpenAI Agents to call list_tasks MCP tool
  - Verify tool calls Phase-2 task endpoint correctly
  - Verify response includes correct user tasks

- [ ] T023 [P] [US1] Integration test: Ownership enforcement in `backend/tests/integration/test_ownership_enforcement.py`
  - User A sends "Delete task 5"
  - Task 5 belongs to User B
  - Verify MCP tool blocks deletion (returns 401 from Phase-2 endpoint)
  - Verify AI responds appropriately (no cross-user access)

**Checkpoint**: User Story 1 complete - users can send messages and get AI responses

---

## Phase 4: User Story 2 - Maintain Chat Conversation History (Priority: P1)

**Goal**: Users can see full conversation history across sessions. Conversation persistence and retrieval.

**Independent Test**:
1. User sends 5 messages in one conversation
2. Close browser/session
3. Retrieve same conversation
4. All 5 messages visible in chronological order with roles (user/assistant) correct

### 4A: Conversation Retrieval Service

- [ ] T024 [US2] Implement chat_service.get_conversation(user_id, conversation_id) in `backend/app/services/chat_service.py`:
  - Query Conversation table by ID
  - Verify user_id ownership
  - Query Message table with conversation_id
  - Return {id, title, messages: [{id, role, content, timestamp}]}
  - Return None if not owned by user

- [ ] T025 [US2] Implement chat_service.list_conversations(user_id, limit=10) in `backend/app/services/chat_service.py`:
  - Query Conversation table filtered by user_id
  - Order by created_at DESC
  - Return [{id, title, created_at, message_count}]

**Acceptance Criteria**:
- ✅ Conversations retrieved correctly with ownership filter
- ✅ Messages in chronological order
- ✅ Roles (user/assistant) preserved
- ✅ Cross-user access prevented

### 4B: Conversation CRUD Endpoints

- [ ] T026 [US2] Implement GET `/api/{user_id}/conversations` endpoint in `backend/app/api/routes/chat.py`:
  - Extract user_id from JWT
  - Call chat_service.list_conversations(user_id)
  - Return [{id, title, created_at, message_count}]
  - Handle 401 if unauthorized

- [ ] T027 [US2] Implement GET `/api/{user_id}/conversations/{id}` endpoint in `backend/app/api/routes/chat.py`:
  - Extract user_id from JWT
  - Call chat_service.get_conversation(user_id, id)
  - Return {id, title, messages: [...]}
  - Return 404 if not found or not owned

- [ ] T028 [US2] Implement DELETE `/api/{user_id}/conversations/{id}` endpoint in `backend/app/api/routes/chat.py`:
  - Extract user_id from JWT
  - Query Conversation by ID
  - Verify ownership (return 404 if not owned)
  - Delete from Conversation table (cascade deletes Messages)
  - Return 204 No Content

**Acceptance Criteria**:
- ✅ List endpoint returns all conversations for authenticated user
- ✅ Get endpoint returns full history with messages
- ✅ Delete endpoint removes conversation + messages
- ✅ All endpoints enforce ownership (404 if not owned, not data leak)

### 4C: Integration Tests for US2

- [ ] T029 [P] [US2] Integration test: Conversation persistence in `backend/tests/integration/test_conversation_crud.py`
  - Create conversation
  - Add 5 messages (user + assistant pairs)
  - Query conversation
  - Verify all 5 messages present in order

- [ ] T030 [P] [US2] Integration test: Conversation isolation in `backend/tests/integration/test_conversation_crud.py`
  - User A creates conversation 1
  - User B tries to GET conversation 1
  - Verify 404 returned (not data leak)

- [ ] T031 [P] [US2] Integration test: List conversations in `backend/tests/integration/test_conversation_crud.py`
  - User creates 3 conversations
  - GET /conversations returns all 3 with metadata
  - Verify order by created_at DESC

**Checkpoint**: User Story 2 complete - conversation history fully functional

---

## Phase 5: User Story 3 - Use AI to Automate Common Task Operations (Priority: P2)

**Goal**: AI understands multi-step commands like "Complete my first 3 tasks" and executes them via MCP tools.

**Independent Test**:
1. User has 5 tasks
2. User sends "Complete all my tasks"
3. AI agent calls complete_task 5 times (one per task)
4. All tasks marked complete
5. AI confirms "Completed 5 tasks"

### 5A: Agent Context & Tool Integration

- [ ] T032 [US3] Enhance OpenAI Agents initialization in chat_service.send_message() to properly handle multi-turn reasoning:
  - Pass full conversation history to agent with role/content pairs
  - Ensure agent can reference previous context when identifying tasks
  - Implement graceful error handling when tool call fails (e.g., task not found)
  - Agent should ask user for clarification instead of failing

- [ ] T033 [US3] Add agent prompt engineering in chat_service to enable bulk operations:
  - System prompt includes guidance: "If user asks to complete/delete multiple tasks, call the tool multiple times"
  - Examples: "User says 'Delete first 3', you should call delete_task 3 times"

**Acceptance Criteria**:
- ✅ Agent makes multiple MCP tool calls for bulk operations
- ✅ Agent gracefully handles failures (task not found → ask user)
- ✅ Agent context includes conversation history
- ✅ No hallucinated task IDs

### 5B: Error Handling for US3

- [ ] T034 [P] [US3] Enhance error handling in MCP tools to return useful error info:
  - Tool returns error details (not just boolean failure)
  - Agent can understand error and respond appropriately to user
  - Example: MCP tool gets 404 → agent responds "Task ID 99 not found, would you like to see all your tasks?"

- [ ] T035 [P] [US3] Add timeout/retry handling in chat_service for slow OpenAI responses:
  - Agent reasoning for bulk operations may take longer
  - Increase timeout to 30+ seconds for multi-step operations
  - Retry logic with exponential backoff (max 3 retries)

**Acceptance Criteria**:
- ✅ Bulk operations complete without errors
- ✅ User receives confirmation of actions taken
- ✅ Failed operations reported gracefully
- ✅ Timeouts handled with retry

### 5C: Integration Tests for US3

- [ ] T036 [P] [US3] Integration test: Bulk task operations in `backend/tests/integration/test_bulk_operations.py`
  - Create 5 tasks for user
  - Send "Complete first 3"
  - Verify 3 tasks marked complete via database query
  - AI response includes count ("Completed 3 tasks")

- [ ] T037 [P] [US3] Integration test: Error recovery in `backend/tests/integration/test_error_recovery.py`
  - User sends "Delete task 999" (doesn't exist)
  - MCP tool returns 404
  - AI responds with helpful message (no crash)
  - Conversation continues normally

**Checkpoint**: User Story 3 complete - bulk operations functional

---

## Phase 6: User Story 4 - Access Chat via Isolated UI Route (Priority: P2)

**Goal**: Chat page at `/chat` (frontend) is isolated from dashboard; no interference with existing Task UI.

**Note**: This story is primarily frontend (Spec-3), but backend tasks ensure API support and isolation testing.

### 6A: Chat Endpoint Documentation & Contracts

- [ ] T038 [US4] Verify chat endpoint contract compliance in `backend/specs/004-ai-chatbot/contracts/chat-endpoint.openapi.yaml`:
  - All 4 endpoints (POST /chat, GET /conversations, GET /conversations/{id}, DELETE /conversations/{id})
  - All error codes (400, 401, 404, 429, 503) properly returned
  - Response schemas match contract

**Acceptance Criteria**:
- ✅ All endpoints match OpenAPI contract
- ✅ Error responses include detail field
- ✅ Status codes correct

### 6B: Isolation Testing

- [ ] T039 [P] [US4] Integration test: Dashboard isolation in `backend/tests/integration/test_frontend_isolation.py`
  - Run Phase-2 task CRUD endpoints (list, create, delete)
  - Simultaneously run new chat endpoints (send message, list conversations)
  - Verify no interference: both continue working correctly
  - No shared state leakage

- [ ] T040 [P] [US4] Integration test: Stateless request handling in `backend/tests/integration/test_stateless.py`
  - Send 3 chat messages from same user to different "instances" (simulate load balancing)
  - Verify conversation history consistent across "instances"
  - No in-memory state issues

**Acceptance Criteria**:
- ✅ Chat and task endpoints work simultaneously
- ✅ No cross-contamination
- ✅ Stateless verified (no global state)

**Checkpoint**: User Story 4 complete - backend ready for frontend integration

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements and quality across all user stories

### 7A: Documentation & DevEx

- [ ] T041 [P] Create quickstart.md in `backend/specs/004-ai-chatbot/quickstart.md`:
  - How to set OPENAI_API_KEY
  - How to make a chat request (curl example)
  - How to test locally
  - Expected responses

- [ ] T042 [P] Update backend README with AI chatbot endpoint documentation

- [ ] T043 [P] Create manual testing checklist in `backend/tests/manual/test_plan.md`:
  - Steps to test chat functionality manually
  - Expected behaviors for each user story

### 7B: Error Handling & Resilience

- [ ] T044 [P] Comprehensive error handling in chat endpoint:
  - All error scenarios return proper HTTP status + detail field
  - No internal stack traces exposed
  - OpenAI API errors → 503 "AI service temporarily unavailable"
  - Database errors → 500 with generic message

- [ ] T045 [P] Add logging for chat operations:
  - Log: chat request received, MCP tool calls, OpenAI response
  - Log errors with context (user_id, conversation_id)
  - Use existing logging framework from Phase-2

### 7C: Security Hardening

- [ ] T046 [P] Input validation for chat messages:
  - Non-empty message required
  - Max message length: 4000 characters
  - Sanitize message content (prevent injection)
  - Validate conversation_id is integer

- [ ] T047 [P] API Security:
  - Verify all endpoints require JWT
  - Verify user_id from JWT (not path)
  - Verify rate limiting prevents abuse
  - Test with expired/invalid JWT → 401

### 7D: Configuration & Deployment

- [ ] T048 Update `backend/.env.example` with all required variables:
  - OPENAI_API_KEY (required)
  - OPENAI_MODEL (default: gpt-4)
  - CHAT_RATE_LIMIT (default: 20)
  - OPENAI_TIMEOUT (default: 30)

- [ ] T049 [P] Add feature flag support (optional):
  - Config: ENABLE_CHAT (default: true)
  - If false: chat endpoints return 503 (allows quick disable)
  - Useful for rollback

### 7E: Final Verification & Regression

- [ ] T050 Run Phase-2 regression tests:
  - All task CRUD endpoints work
  - All task tests pass
  - No changes to task.py, user.py, task_service.py
  - No schema changes to Task/User tables

- [ ] T051 [P] Run full test suite:
  - All unit tests pass
  - All integration tests pass
  - All 4 user stories independently testable

- [ ] T052 [P] Manual end-to-end test:
  - Create conversation and send 3 messages
  - Verify all visible in history
  - Create task via chat command
  - Verify task in dashboard (Phase-2 endpoint)
  - Delete conversation
  - Verify dashboard still works

**Acceptance Criteria**:
- ✅ Phase-2 unaffected (all tests pass)
- ✅ All new tests pass
- ✅ All 4 user stories independently testable
- ✅ Ready for production deployment

---

## Dependencies & Execution Strategy

### Phase Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundation) ← BLOCKS all user stories
    ↓
Phase 3 (US1 - Ask AI) ─┐
Phase 4 (US2 - History) │ Can run in PARALLEL
Phase 5 (US3 - Bulk)   │ after Phase 2
Phase 6 (US4 - Isolation) ┘
    ↓
Phase 7 (Polish)
```

### Parallel Opportunities

**Phase 1**: All [P] tasks can run in parallel (independent files)

**Phase 2**:
- Tasks T007-T010 can run in parallel (different files)
- Tasks T011-T013 can run in parallel (MCP tools)
- Task T015-T016 can run in parallel

**Phase 3-6**: Each user story can be worked on independently once Phase 2 completes
- Within Phase 3: T018-T023 can run partially in parallel (T018 must complete before T019)
- Within Phase 4: T024-T031 can run in parallel (service before endpoints)
- Within Phase 5: T032-T037 can run in parallel (implementation before tests)
- Within Phase 6: T038-T040 can run in parallel

**Example: Two developers**
- Developer 1: Phase 2 (Database & MCP) + Phase 3 (Chat endpoint)
- Developer 2: Phase 4 (Conversation CRUD) + Phase 5 (Bulk operations)
- Both: Phase 7 (Polish & testing)

### MVP Scope (First Iteration)

**Minimum for demo**: Phases 1-2 + Phase 3 (User Story 1 only)
- User can send message → AI processes → response returned
- Core chat functionality works
- Rate limit basic

**Recommended for first PR**: Phases 1-2 + Phase 3-4 (US1 + US2)
- Chat with history retention
- Conversation list/retrieval
- Independent test of each story

**Full release**: All phases 1-7
- All 4 user stories
- Error handling
- Documentation
- Security

### Task Execution Sequence

```
1. Complete Phase 1 (Setup) - ~1-2 hours
2. Complete Phase 2 (Foundation) - ~4-6 hours
   Checkpoint: Foundation ready, all tests pass
3. START Phase 3-6 in parallel or sequence:
   - Phase 3 (US1): ~3-4 hours
   - Phase 4 (US2): ~3-4 hours
   - Phase 5 (US3): ~2-3 hours
   - Phase 6 (US4): ~1-2 hours
4. Complete Phase 7 (Polish) - ~2-3 hours
   Final Checkpoint: All tests pass, Phase-2 regression tests pass, ready to deploy
```

**Total Estimated Time**:
- Sequential: 19-24 hours
- With 2 developers (parallel): 10-12 hours

---

## Task Status Tracking

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Setup | ⏳ Ready | Start immediately |
| Phase 2: Foundation | ⏳ Blocked by Phase 1 | Start after Phase 1 complete |
| Phase 3: US1 | ⏳ Blocked by Phase 2 | MVP story - prioritize |
| Phase 4: US2 | ⏳ Blocked by Phase 2 | Add to first PR |
| Phase 5: US3 | ⏳ Blocked by Phase 2 | Nice to have, Phase 2 PR |
| Phase 6: US4 | ⏳ Blocked by Phase 2 | Coordination with frontend |
| Phase 7: Polish | ⏳ Blocked by Phase 6 | Final QA + deployment prep |

---

## Rollback Checklist (If Issues)

If critical bug discovered after deployment:

- [ ] Set `ENABLE_CHAT=false` in environment (disables chat endpoint)
- [ ] Verify Phase-2 task endpoints still work (curl `/api/{user_id}/tasks`)
- [ ] If database corruption: `DROP TABLE IF EXISTS message, conversation;`
- [ ] Backend restarts as Phase-2 only
- [ ] Time to rollback: < 5 minutes

---

## Quality Checklist Before Merge

- [ ] All Phase 2-7 tasks complete
- [ ] All tests pass (unit + integration)
- [ ] Phase-2 regression tests pass
- [ ] No Phase-2 files modified
- [ ] All 4 user stories independently testable
- [ ] Manual E2E test successful
- [ ] Code reviewed for security
- [ ] Documentation updated
- [ ] Rollback plan documented
- [ ] Ready for production deployment

---

**Next Step**: Begin Phase 1 Setup tasks. Each task includes its own acceptance criteria and file paths for unambiguous implementation.

**Command**: `grep "- \[ \] T" specs/004-ai-chatbot/tasks.md | wc -l` to count total tasks.

**Total Tasks**: 52 tasks across 7 phases (independently executable)
