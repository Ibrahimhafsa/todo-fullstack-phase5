---
id: 0002
title: Phase-3 AI Chatbot Constitution Creation
stage: constitution
date: 2026-02-18
surface: agent
model: claude-haiku-4-5-20251001
feature: 004-ai-chatbot
branch: main
user: system
command: /sp.constitution
labels: ["governance","phase3","chatbot","security","mcp"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - null
---

## Prompt

We are starting Phase-3 (AI Chatbot) of an existing full-stack Todo application.

IMPORTANT:
Before writing this constitution, you MUST carefully analyze and understand the entire existing Phase-2 project structure.

Read and understand:
- /backend (FastAPI, SQLModel, Neon DB, JWT auth, task CRUD)
- /frontend (Next.js 16 App Router, Tailwind, Better Auth, task dashboard UI)
- All authentication flow
- All task CRUD endpoints
- Database models
- JWT enforcement logic
- Ownership rules

Phase-2 is fully working and deployed.
You MUST NOT break or rewrite any existing working logic.

Your task:
Create a Phase-3 Constitution that governs adding an AI Chatbot system using:

- OpenAI Agents SDK
- MCP Server (Official MCP SDK)
- Stateless chat endpoint
- Conversation + Message DB models
- OpenAI ChatKit frontend integration

This constitution must:

1) Lock Phase-2 as read-only and extension-only.
2) Explicitly forbid modifying working auth and task CRUD logic.
3) Require reusing existing task logic inside MCP tools (no duplication).
4) Enforce JWT security and ownership rules for chat endpoints.
5) Enforce stateless architecture.
6) Define strict database safety rules.
7) Define frontend isolation rules (Chat UI must not break dashboard).
8) Define tool governance rules (only allowed MCP tools).
9) Include explicit forbidden features (no advanced features beyond basic level).
10) Define clear success criteria for Phase-3.

This constitution must:
- Preserve all prior principles from Spec-1, Spec-2, and Spec-3.
- Be structured cleanly.
- Include Non-Negotiable Safety Rules.
- Be written in professional governance format.
- Be suitable for Spec-Kit Plus workflow.

Do NOT implement anything.
Only generate the Phase-3 Constitution document.

This constitution must ensure Phase-3 extends the system safely without regression.

## Response snapshot

Successfully created Phase-3 Constitution (v2.0.0) with comprehensive governance for AI Chatbot system:

**Key sections added**:
- 10 new core principles (XVI-XXV) covering:
  - Phase-2 read-only mandate
  - Stateless chat architecture
  - JWT security for chat endpoints
  - Conversation ownership rules
  - MCP tool governance (explicit allowlist)
  - Chat-task integration via MCP
  - Chat frontend isolation
  - Conversation persistence
  - Error handling patterns
  - OpenAI integration security

**Phase-2 protection mechanisms**:
- Explicit lockdown: "NO modifications to existing task CRUD endpoints"
- Mandatory composition: "Phase-3/4 features MUST use existing endpoints via MCP"
- Bug fix gating: "Only if documented in ADR with security impact analysis"
- Breaking change prohibition: "Breaking changes to task logic are FORBIDDEN"

**MCP tool governance**:
- Explicit allowlist: only 6 tools (list, get, create, update, delete, complete tasks)
- Forbidden patterns: direct DB access, file system ops, system commands
- Reuse mandate: tools MUST wrap existing REST endpoints
- Ownership enforcement: tools MUST validate user ownership before executing

**Chat-specific rules**:
- Stateless: "No session state stored in backend memory"
- Isolated: "Chat UI MUST be implemented in separate route"
- Secure: "JWT required for all chat endpoints"
- Limited: "Advanced features beyond basic chat are FORBIDDEN"

**Database schema included**:
- Conversation model with user_id, title, timestamps
- Message model with conversation_id, user_id, role, content
- Indexes on (user_id, created_at) for performance

**Success criteria defined** with 13 testable checkpoints for Phase-4 implementation.

## Outcome

- ✅ Impact: Complete constitutional framework for Phase-3 AI Chatbot, protecting Phase-2 production code, enabling MCP-based task integration, enforcing JWT security and user ownership throughout
- 🧪 Tests: Constitution document passes all validation checks (no unresolved placeholders, proper formatting, semantic clarity, testable principles)
- 📁 Files: .specify/memory/constitution.md (updated v1.2.0 → 2.0.0)
- 🔁 Next prompts: Phase-4 specification creation, Phase-4 architecture planning, task breakdown
- 🧠 Reflection: Constitution successfully balances extensibility with stability through explicit phase lockdown, tool governance allowlist, and ownership enforcement patterns that mirror Phase-2 task security

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - Comprehensive governance framework established
- Prompt variant (if applicable): null
- Next experiment: Phase-4 spec creation with MCP tool definitions as formal interfaces

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
