---
id: 0001
title: Specify chat UI feature
stage: spec
date: 2026-02-20
surface: agent
model: claude-haiku-4-5-20251001
feature: 005-chat-ui
branch: 005-chat-ui
user: default
command: /sp.specify
labels: ["chat-ui", "frontend", "spec", "openai-chatkit"]
links:
  spec: /specs/005-chat-ui/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - /specs/005-chat-ui/spec.md
 - /specs/005-chat-ui/checklists/requirements.md
tests:
 - Spec validation checklist (13/13 items passing)
---

## Prompt

SPEC-5 — Chat UI with OpenAI ChatKit (Frontend Only)

Goal:
Build a production-ready conversational UI for the Todo AI Assistant using OpenAI ChatKit that connects to the Spec-4 backend agent.

Scope: FRONTEND ONLY — no backend changes allowed.

Requirements:

1. Chat Interface
- Install and configure OpenAI ChatKit
- Provide a modern chat UI (message bubbles, input box, send button)
- Show conversation history within the session
- Display user and assistant messages clearly
- Support loading state while waiting for response
- Support error state with retry

2. Backend Integration
- Connect to existing endpoint:
  POST /api/{user_id}/chat
- Include JWT token in Authorization header
- Extract user_id from authenticated session
- Maintain conversation_id returned by backend
- Send conversation_id on subsequent messages

3. Tool Response Rendering
- Display natural language responses from the agent
- Format multi-line responses cleanly
- Ensure no raw JSON/tool output shown to user
- Support long responses with scrolling

4. Conversation Management
- Store current conversation_id in React state
- Reset conversation when user logs out
- No server state stored on frontend

5. Security Rules
- Do NOT expose OpenAI API key in frontend
- Frontend only communicates with backend
- Use existing authentication system

6. Domain Allowlist Preparation
- Prepare for hosted ChatKit domain key
- Support environment variable:
  NEXT_PUBLIC_OPENAI_DOMAIN_KEY

7. Deployment Readiness
- Compatible with Vercel deployment
- Mobile responsive design
- Works on desktop and mobile

Technology Constraints:
- Next.js 16+ App Router
- TypeScript
- Tailwind CSS
- OpenAI ChatKit
- Existing Better Auth integration

Folder Safety Rules:
- All work MUST occur inside /frontend
- Do NOT modify backend files
- Do NOT recreate existing auth or dashboard
- Chat UI should exist as a new route/page (e.g., /chat)

Explicitly Forbidden:
- Any changes to Spec-4 backend
- Any database changes
- Any task CRUD UI changes
- Direct OpenAI calls from frontend

Success Criteria:
- User can send message from chat UI
- Backend agent processes request
- Tool actions executed via MCP
- Assistant response displayed correctly
- Conversation persists across messages
- Works locally and after Vercel deployment

## Response snapshot

✅ Specification created successfully for SPEC-005: Chat UI with OpenAI ChatKit

**Created artifacts:**
- Feature spec: `/specs/005-chat-ui/spec.md` (complete with 4 prioritized user stories, 15 functional requirements, 8 success criteria)
- Quality checklist: `/specs/005-chat-ui/checklists/requirements.md` (13/13 items passing)
- PHR: This prompt history record

**Key highlights from spec:**
- 2 P1 stories (Send/Receive Messages, Maintain Context) + 2 P2 stories (Error Handling, Mobile Responsiveness)
- 15 functional requirements covering chat UI, backend integration, security, responsiveness
- 8 measurable success criteria with specific metrics (5-second response time, viewport testing, conversation depth)
- Comprehensive edge cases and constraints identified
- Clear separation of frontend-only scope with no backend modifications allowed

## Outcome

- ✅ Impact: Feature specification complete with clear user stories, requirements, and success criteria. Ready for architecture planning phase.
- 🧪 Tests: Specification quality checklist: 13/13 items passing (100%). All requirements testable and unambiguous.
- 📁 Files: 2 artifacts created (spec.md + requirements.md). All placeholders resolved.
- 🔁 Next prompts: `/sp.plan` to create architecture and design artifacts for implementation
- 🧠 Reflection: Specification covers all 7 original requirements and provides clear acceptance criteria. Frontend-only scope strictly maintained. Ready to proceed to planning phase.

## Evaluation notes (flywheel)

- Failure modes observed: None - specification is complete and validated
- Graders run and results (PASS/FAIL): Specification Quality Checklist: PASS (13/13)
- Prompt variant (if applicable): Base specification from user requirements
- Next experiment: Execute `/sp.plan` to generate architecture and implementation plan
