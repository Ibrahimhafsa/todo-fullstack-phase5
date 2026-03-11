---
id: 0002
title: Spec-4 Implementation Plan & Architecture
stage: plan
date: 2026-02-18
surface: agent
model: claude-haiku-4-5-20251001
feature: 004-ai-chatbot
branch: main
user: system
command: /sp.plan
labels: ["architecture","backend","safety","phase-separation","mcp"]
links:
  spec: specs/004-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/004-ai-chatbot/plan.md
tests:
  - null
---

## Prompt

Create a safe implementation plan for Spec-4.

Constraints:
- Phase-2 backend is production-ready and must not break.
- All new work must be isolated.
- MCP tools must wrap existing task logic.
- No duplication allowed.

The plan must:
- Break into atomic steps
- Separate DB layer changes
- Separate MCP layer
- Separate Agent layer
- Separate Chat endpoint
- Include migration steps
- Include dependency installation step
- Include testing strategy

Add rollback strategy in case chat endpoint fails.

Do NOT generate code.
Generate a structured step-by-step execution plan.

## Response snapshot

Successfully created comprehensive Phase-1 Implementation Plan (plan.md) with:

**Technical Context**:
- Python 3.11+, FastAPI, SQLModel, Neon PostgreSQL
- New dependencies: openai-agents, mcp SDKs
- Performance targets: <30s p95 (OpenAI-bounded), <100ms DB
- Scale: MVP 10+ concurrent sessions, 1-10 users

**Constitution Check**:
✅ PASS - All 13 Constitution principles verified:
- JWT enforcement (Principle I, XVIII)
- Phase-2 read-only (Principle XVI)
- Ownership enforcement (Principle VII, XIX)
- Stateless architecture (Principle XVII)
- MCP tool governance (Principle XX, XXI)
- Error handling (Principle XXIV)
- OpenAI security (Principle XXV)

**Project Structure**:
- Source: backend/app/models/, services/, api/routes/, api/mcp_server/ (7 new files)
- Tests: 6 new test modules (unit + integration)
- No changes to existing Phase-2 code

**Phase 0: Research** (6 research tasks)
- OpenAI Agents SDK integration pattern
- Official MCP SDK tool definition
- FastAPI + SQLModel database initialization
- Rate limiting patterns (per-user, stateless)
- MCP tool error handling
- Conversation context window management

**Phase 1: Design & Contracts** (4 design outputs)
- data-model.md: Conversation (id, user_id, title, timestamps), Message (id, conversation_id, user_id, role, content, timestamp) with composite index on (user_id, created_at)
- contracts/chat-endpoint.openapi.yaml: POST/GET/DELETE endpoints with error codes
- contracts/mcp-tools.interface.yaml: 6 tool definitions (list/get/create/update/delete/complete) with input/output/error specs
- contracts/conversation-crud.openapi.yaml: REST CRUD patterns
- quickstart.md: Developer guide

**Phase 2: Implementation Breakdown** (6 layers, 18+ atomic tasks)

Layer 1 (DB):
- Task 1.1: Install dependencies (openai-agents, mcp)
- Task 1.2: Create Conversation model + unit test
- Task 1.3: Create Message model + unit test
- Task 1.4: Database initialization on startup

Layer 2 (MCP Tools):
- Task 2.1: Implement 6 MCP tools wrapping Phase-2 task_service (list/get/create/update/delete/complete)
- Task 2.2: Initialize MCP Server
- Task 2.3: Unit test MCP tools (verify ownership, error wrapping)

Layer 3 (Chat Service):
- Task 3.1: Implement send_message() (store user msg, call OpenAI, store response)
- Task 3.2: Implement per-user rate limiting (20 req/min)
- Task 3.3: Unit test chat service (mocked OpenAI)

Layer 4 (Chat Endpoints):
- Task 4.1: Implement POST /api/{user_id}/chat (send message)
- Task 4.2: Implement conversation CRUD (GET list, GET single, DELETE)
- Task 4.3: Register routes in FastAPI app

Layer 5 (Integration Tests):
- Task 5.1: E2E chat flow test
- Task 5.2: MCP tool integration test (calls Phase-2 endpoints)
- Task 5.3: Conversation management test
- Task 5.4: Error scenarios (JWT, rate limit, OpenAI down)

Layer 6 (Safety & Rollback):
- Task 6.1: Verify Phase-2 regression tests PASS
- Task 6.2: Document rollback procedures

**Safety & Rollback**:

Pre-deployment:
- Run Phase-2 regression tests (all CRUD endpoints)
- Run new integration tests
- Verify no schema changes to Task/User

Rollback Option A (fast, disable chat):
- Set ENABLE_CHAT=false
- Chat endpoint returns 503
- Phase-2 continues normally
- No data loss

Rollback Option B (database cleanup):
- DROP TABLE IF EXISTS message, conversation;
- Backend restarts as Phase-2 only
- Conversation data orphaned but not destroyed

Rollback Option C (version rollback):
- Deploy previous backend commit
- Phase-2 continues normally

**Testing Strategy**:
- Unit tests (Layer 1-3): Model behavior, tool wrapping, rate limiting
- Integration tests (Layer 4-5): E2E chat flow, MCP + Phase-2, ownership, errors
- Manual tests: UI chat works, dashboard isolation, expired JWT
- Regression tests: Phase-2 unaffected

**Deployment Steps** (10-step safe deployment):
1. Create feature branch
2. Implement tasks (Layer 1-5)
3. Run all tests
4. Create PR with results
5. Deploy to staging
6. Manual test in staging
7. Deploy prod with ENABLE_CHAT=false
8. Verify Phase-2 works
9. Enable chat: ENABLE_CHAT=true
10. Monitor 24h before merge

## Outcome

- ✅ Impact: Comprehensive Phase-1 plan that isolates all new code, enforces Phase-2 safety through explicit structure, enables safe rollback if issues arise, separates implementation into 6 logical layers with clear layer dependencies
- 🧪 Tests: Constitution Check passed all 13 principles; 4 design phases defined; 6 research tasks identified; 18+ atomic implementation tasks
- 📁 Files: specs/004-ai-chatbot/plan.md (1500+ lines with complete structure)
- 🔁 Next prompts: `/sp.plan` Phase 0 (research), `/sp.tasks` for detailed task breakdown with time estimates
- 🧠 Reflection: Plan successfully ensures "zero risk to Phase-2" through layered architecture (DB → MCP → Service → Endpoints), explicit rollback procedures, and comprehensive testing strategy spanning unit/integration/regression/manual

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - Plan ready for Phase 0 research
- Prompt variant (if applicable): null
- Next experiment: Begin Phase 0 research tasks to resolve SDK integration patterns

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
