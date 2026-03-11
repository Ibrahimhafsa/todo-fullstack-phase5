---
id: 0001
title: Spec-4 MCP Chatbot Backend Specification
stage: spec
date: 2026-02-18
surface: agent
model: claude-haiku-4-5-20251001
feature: 004-ai-chatbot
branch: main
user: system
command: /sp.specify
labels: ["backend","chatbot","mcp","agents","openai","phase4"]
links:
  spec: specs/004-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/004-ai-chatbot/spec.md
  - specs/004-ai-chatbot/checklists/requirements.md
tests:
  - null
---

## Prompt

SPEC-4 — MCP Tools & Agent Backend

IMPORTANT:
Before writing this specification, you MUST review and understand the entire existing Phase-2 backend.

You must read:
- app/models (Task, User)
- app/api/routes/tasks.py
- JWT dependency logic
- get_current_user dependency
- DB session handling
- Ownership enforcement logic

Spec-4 must EXTEND Phase-2.
It must NOT modify or rewrite working task CRUD logic.

Purpose:
Add AI Brain Layer using:
- OpenAI Agents SDK
- Official MCP SDK
- Stateless architecture
- Conversation + Message persistence

Scope (Backend ONLY):

1) Install:
   - openai-agents SDK
   - official MCP SDK

2) Create new database models:
   - Conversation
   - Message

3) Create MCP Tool Layer:
   Tools:
   - add_task
   - list_tasks
   - complete_task
   - delete_task
   - update_task

CRITICAL RULE:
MCP tools MUST reuse existing task service logic.
They MUST NOT duplicate CRUD logic.

4) Create new endpoint:
POST /api/{user_id}/chat

5) Stateless Chat Flow:
- Receive message
- Fetch conversation history
- Store user message
- Run agent
- Agent calls MCP tools
- Store assistant response
- Return structured response

6) Agent Behavior:
- Use tools appropriately
- Confirm actions politely
- Handle task-not-found gracefully
- No hallucinated task IDs

STRICTLY FORBIDDEN:
- No frontend changes
- No task schema modification
- No auth modification
- No duplication of CRUD logic
- No global state
- No in-memory chat history

Success Criteria:
- Chat endpoint works with JWT
- Agent calls tools correctly
- DB persists conversation + messages
- Stateless request cycle verified

Do NOT implement.
Only generate a complete Spec-4 specification document.

## Response snapshot

Successfully created comprehensive Spec-4: AI Chatbot with MCP Tools & Agent Backend specification with:

**4 User Stories** (P1-P2):
- US1: Ask AI to help manage tasks (P1) - core value
- US2: Maintain chat history (P1) - persistence
- US3: Automate common operations (P2) - bulk actions
- US4: Access via isolated UI route (P2) - infrastructure

**20 Functional Requirements**:
- FR-001 to FR-020 covering chat endpoint, MCP tools, ownership, stateless architecture
- FR-007 explicitly mandates reuse of Phase-2 task endpoints (no duplication)
- FR-017-019 explicitly forbid modifying Phase-2 logic

**2 Key Entities**:
- Conversation (id, user_id, title, timestamps)
- Message (id, conversation_id, user_id, role, content, timestamp)
- MCP Tool (code abstraction, wraps Phase-2 endpoints)

**8 Success Criteria**:
- 30-second latency (SC-001)
- MCP tools complete operations (SC-002)
- Conversation persists 24h+ (SC-003)
- Ownership enforced (SC-004)
- Stateless multi-instance (SC-005)
- Rate limiting 20/min per user (SC-006)
- OpenAI failures graceful (SC-007)
- Dashboard unaffected (SC-008)

**Technology Stack**:
- OpenAI Agents SDK, Official MCP SDK, FastAPI, SQLModel, Neon PostgreSQL
- Config: OPENAI_API_KEY, OPENAI_MODEL, CHAT_RATE_LIMIT, OPENAI_TIMEOUT

**Scope Clarity**:
- In-scope: Backend models, MCP layer, chat endpoint, conversation CRUD
- Out-of-scope: Frontend UI (Spec-3), task modification, auth changes
- Edge cases: malformed commands, cross-user boundary, API down, JWT expiration
- Assumptions: OpenAI available, simple tools, single-user alpha, ≤100 msg/conversation

**Quality Validation**:
- ✅ PASS: All 4 content quality items
- ✅ PASS: All 8 requirement completeness items
- ✅ PASS: All 4 feature readiness items
- ✅ PASS: No [NEEDS CLARIFICATION] markers
- ✅ PASS: Spec ready for planning phase

## Outcome

- ✅ Impact: Comprehensive specification for AI Chatbot backend extending Phase-2 without modification. Enforces stateless architecture, MCP tool reuse, and ownership security.
- 🧪 Tests: Specification validation checklist 16/16 items PASS; quality assessment complete
- 📁 Files: specs/004-ai-chatbot/spec.md (2000+ lines), specs/004-ai-chatbot/checklists/requirements.md
- 🔁 Next prompts: `/sp.plan` for architecture design, `/sp.tasks` for task breakdown
- 🧠 Reflection: Specification successfully balances feature ambition (multi-turn agent) with Phase-2 protection (explicit no-modification mandates), establishes clear MCP tool boundary (6 tools, existing endpoints only), and defines measurable success criteria (latency, persistence, ownership, statelessness)

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - Comprehensive specification with zero blocking issues
- Prompt variant (if applicable): null
- Next experiment: Architecture planning with explicit MCP tool interface definitions

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
