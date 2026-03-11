---
id: 0002
title: Plan chat UI architecture and design
stage: plan
date: 2026-02-20
surface: agent
model: claude-haiku-4-5-20251001
feature: 005-chat-ui
branch: 005-chat-ui
user: default
command: /sp.plan
labels: ["chat-ui", "frontend", "plan", "architecture", "openai-chatkit"]
links:
  spec: /specs/005-chat-ui/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - /specs/005-chat-ui/plan.md
 - /specs/005-chat-ui/research.md
 - /specs/005-chat-ui/data-model.md
 - /specs/005-chat-ui/quickstart.md
 - /specs/005-chat-ui/contracts/chat-api.md
tests:
 - Constitutional compliance check: PASS (all 10 principles validated)
 - API contract specification: COMPLETE (4 endpoints documented)
 - Component architecture: DEFINED (6 main components)
---

## Prompt

Create an implementation plan for SPEC-5 Chat UI with OpenAI ChatKit that integrates with the existing Spec-4 backend agent.

Plan must:

1. Respect Phase-2 and Spec-4 safety
- No backend modifications
- No database changes
- No breaking existing dashboard

2. Include ChatKit setup
- Installation steps
- Configuration
- Environment variables

3. Define frontend architecture
- React components
- State management for messages
- Conversation ID handling
- Authentication integration

4. Define API integration strategy
- How to call POST /api/{user_id}/chat
- JWT token handling
- Error handling and retries

5. Define UI structure
- Chat page layout
- Message components
- Input component
- Loading indicators

6. Include domain allowlist setup for production

7. Include Vercel deployment preparation
- Environment variables
- Production configuration

Output must be structured, step-by-step, and executable by Claude Code.

Focus ONLY on frontend implementation.

## Response snapshot

✅ **Implementation Plan Complete** — Comprehensive frontend-only design for SPEC-5 Chat UI

**Deliverables** (5 artifacts):

1. **plan.md** — Master implementation plan with:
   - Technical context (TypeScript 5.x, React 19, Next.js 16)
   - Constitutional compliance check (10/10 principles ✅)
   - Project structure (frontend-only, no backend modifications)
   - Phase 0-1 research, design, and deployment guidance

2. **research.md** — Phase 0 research findings:
   - ChatKit package availability verified
   - JWT token retrieval strategy documented
   - Backend API contract reverse-engineered
   - Environment variable configuration defined
   - Error handling and rate limiting strategy

3. **data-model.md** — Phase 1 design artifacts:
   - Frontend data model (Message, Conversation, ChatUIState)
   - Component architecture (ChatContainer, MessageBubble, ChatInput, etc.)
   - API request/response models
   - Custom hooks (useChat, useJWTToken)
   - Type definitions and validation rules

4. **quickstart.md** — Phase 1 integration guide:
   - 7-step setup procedure (install, env vars, create components)
   - Complete implementation code for all components
   - Testing checklist and test cases
   - Vercel deployment instructions

5. **contracts/chat-api.md** — Phase 1 API specifications:
   - 4 endpoint contracts (POST /chat, GET /conversations, GET /{id}, DELETE /{id})
   - Request/response models with validation
   - Error handling and status codes
   - Rate limiting (20 req/min per user)
   - Authentication and ownership validation

## Outcome

- ✅ Impact: Comprehensive implementation plan enables immediate frontend development. No ambiguity; all technical decisions documented with rationale. Constitutional principles verified; zero violations.
- 🧪 Tests: Constitutional compliance check (10/10 principles passing), API contract validation (4 endpoints specified), Component architecture review (6 components defined with PSL), Data model validation (all entities with constraints defined)
- 📁 Files: 5 files created (1 plan + 1 research + 1 data-model + 1 quickstart + 1 contract), ~2000 lines of documentation, all templates resolved
- 🔁 Next prompts: `/sp.tasks` to generate actionable tasks.md for Phase 2 implementation
- 🧠 Reflection: Plan balances comprehensive guidance with executable clarity. All technical decisions justified by research phase. Frontend isolation maintained per Constitution XXII. Ready for immediate implementation.

## Evaluation notes (flywheel)

- Failure modes observed: None - all NEEDS CLARIFICATION markers resolved in research.md
- Graders run and results (PASS/FAIL): Constitutional Check: PASS (Principle XVI, XVII, XVIII, XXII all satisfied); API Contract Specification: PASS (4 endpoints fully specified); Component Design: PASS (all 6 components with responsibilities and pseudo-code)
- Prompt variant (if applicable): Base planning workflow with Spec-4 backend integration focus
- Next experiment: Execute `/sp.tasks` to generate implementation tasks (estimated 25-30 tasks for full feature)
