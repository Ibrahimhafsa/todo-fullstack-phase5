# Chat API Contracts (SPEC-5)

**API Version**: 1.0.0
**Backend**: FastAPI (Python)
**Frontend**: Next.js 16 + React 19 + TypeScript
**Date**: 2026-02-20

## Overview

This document defines the API contracts between the frontend chat UI (SPEC-5) and the backend chat service (Spec-4). All endpoints require JWT authentication.

**Base URL**: `http://localhost:8000` (local) or `https://api.production.com` (production)

**Authentication**: JWT Bearer token in `Authorization` header
```
Authorization: Bearer <token>
```

---

## Endpoints

### 1. Send Chat Message

Sends a message to the AI chatbot and receives a response.

**Endpoint**:
```
POST /api/{user_id}/chat
```

**Authentication**: Required (JWT)

**Path Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` | string | Yes | Authenticated user ID (must match JWT) |

**Request Body**:
```json
{
  "conversation_id": null,
  "message": "Help me organize my tasks"
}
```

**Request Fields**:
| Name | Type | Required | Description | Constraints |
|------|------|----------|-------------|-------------|
| `conversation_id` | number \| null | No | ID of existing conversation | Null for new conversation; must exist and belong to user if provided |
| `message` | string | Yes | User's message | Non-empty, max 10,000 characters |

**Success Response (200 OK)**:
```json
{
  "message_id": 145,
  "conversation_id": 42,
  "role": "assistant",
  "content": "I can help you organize your tasks. Here are 3 suggestions:\n1. Create a project list\n2. Prioritize by importance\n3. Set deadlines",
  "timestamp": "2026-02-20T14:32:15Z"
}
```

**Response Fields**:
| Name | Type | Description |
|------|------|-------------|
| `message_id` | number | Unique ID for this response message |
| `conversation_id` | number | Conversation this belongs to (new or existing) |
| `role` | string | Always "assistant" |
| `content` | string | Assistant's response text; may contain newlines |
| `timestamp` | string | ISO 8601 timestamp (server time) |

**Error Responses**:

**400 Bad Request** — Invalid message:
```json
{
  "detail": "Message cannot be empty"
}
```

**401 Unauthorized** — JWT mismatch:
```json
{
  "detail": "User ID mismatch"
}
```

**404 Not Found** — Conversation doesn't exist or not owned:
```json
{
  "detail": "Conversation not found"
}
```

**429 Too Many Requests** — Rate limit exceeded:
```json
{
  "detail": "Rate limit exceeded: max 20 requests per minute"
}
```

**503 Service Unavailable** — OpenAI API down:
```json
{
  "detail": "Chat service temporarily unavailable"
}
```

**Behavior**:

1. **Authentication Check** (FR-003):
   - Verify JWT token is valid
   - Verify `user_id` in path matches JWT claim
   - Return 401 if mismatch

2. **Rate Limiting** (FR-011):
   - Enforce 20 requests/min per user
   - Return 429 if exceeded

3. **Message Validation** (FR-001):
   - Check message is non-empty
   - Strip whitespace and check again
   - Return 400 if invalid

4. **Conversation Management** (FR-002, FR-003):
   - If `conversation_id` is null: create new conversation
   - If `conversation_id` provided: verify it exists and belongs to user
   - Return 404 if conversation doesn't exist or not owned

5. **Message Storage** (FR-004):
   - Store user message to database
   - Store metadata (timestamp, user_id)

6. **OpenAI Processing** (FR-005, FR-006):
   - Call OpenAI Agent with conversation history
   - Pass conversation_id to agent for context
   - Receive response from agent

7. **Response Storage** (FR-007):
   - Store assistant message to database
   - Include all metadata

8. **Response** (FR-008, FR-009):
   - Return ChatResponse with all fields
   - Include timestamp from server

**Example Request/Response**:

```bash
# Request
curl -X POST http://localhost:8000/api/123/chat \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": null,
    "message": "Create a task for tomorrow"
  }'

# Response
{
  "message_id": 146,
  "conversation_id": 43,
  "role": "assistant",
  "content": "I'll help you create a task for tomorrow. Do you want me to:\n1. Add it to your existing project\n2. Create a new project first\n3. Set a specific time",
  "timestamp": "2026-02-20T14:35:22Z"
}
```

---

### 2. List Conversations

Retrieves all conversations for the authenticated user.

**Endpoint**:
```
GET /api/{user_id}/conversations
```

**Authentication**: Required (JWT)

**Path Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` | string | Yes | Authenticated user ID (must match JWT) |

**Query Parameters**: None

**Success Response (200 OK)**:
```json
[
  {
    "id": 42,
    "title": null,
    "created_at": "2026-02-19T10:00:00Z",
    "message_count": 5
  },
  {
    "id": 43,
    "title": null,
    "created_at": "2026-02-20T14:30:00Z",
    "message_count": 2
  }
]
```

**Response Format**:
Array of ConversationSummary objects:
| Name | Type | Description |
|------|------|-------------|
| `id` | number | Unique conversation ID |
| `title` | string \| null | Optional human-readable title |
| `created_at` | string | ISO 8601 creation timestamp |
| `message_count` | number | Count of messages in conversation |

**Error Responses**:

**401 Unauthorized** — JWT mismatch:
```json
{
  "detail": "User ID mismatch"
}
```

**Behavior**:
- Query database for all conversations where `user_id` matches
- Count messages for each conversation
- Return sorted by `created_at` (newest first)
- Return empty array if no conversations

---

### 3. Get Conversation Details

Retrieves a specific conversation with all messages.

**Endpoint**:
```
GET /api/{user_id}/conversations/{conversation_id}
```

**Authentication**: Required (JWT)

**Path Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` | string | Yes | Authenticated user ID |
| `conversation_id` | number | Yes | Conversation ID |

**Success Response (200 OK)**:
```json
{
  "id": 42,
  "title": null,
  "created_at": "2026-02-19T10:00:00Z",
  "messages": [
    {
      "id": 100,
      "role": "user",
      "content": "Help me organize my tasks",
      "timestamp": "2026-02-19T10:01:00Z"
    },
    {
      "id": 101,
      "role": "assistant",
      "content": "Sure! I can help you organize. Let's start with...",
      "timestamp": "2026-02-19T10:02:00Z"
    }
  ]
}
```

**Response Format**:
ConversationDetail object:
| Name | Type | Description |
|------|------|-------------|
| `id` | number | Conversation ID |
| `title` | string \| null | Optional title |
| `created_at` | string | ISO 8601 creation timestamp |
| `messages` | array | Array of Message objects |

**Message Object**:
| Name | Type | Description |
|------|------|-------------|
| `id` | number | Message ID |
| `role` | string | "user" or "assistant" |
| `content` | string | Message text |
| `timestamp` | string | ISO 8601 creation timestamp |

**Error Responses**:

**401 Unauthorized** — JWT mismatch:
```json
{
  "detail": "User ID mismatch"
}
```

**404 Not Found** — Conversation not found or not owned:
```json
{
  "detail": "Conversation not found"
}
```

**Behavior**:
- Query for conversation by ID and user_id
- Return 404 if not found OR not owned by user (no info leakage)
- Query all messages for conversation (ordered by created_at)
- Return with all messages

---

### 4. Delete Conversation

Deletes a conversation and all its messages.

**Endpoint**:
```
DELETE /api/{user_id}/conversations/{conversation_id}
```

**Authentication**: Required (JWT)

**Path Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` | string | Yes | Authenticated user ID |
| `conversation_id` | number | Yes | Conversation ID |

**Request Body**: Empty

**Success Response (204 No Content)**:
```
[No body - just 204 status]
```

**Error Responses**:

**401 Unauthorized** — JWT mismatch:
```json
{
  "detail": "User ID mismatch"
}
```

**404 Not Found** — Conversation not found or not owned:
```json
{
  "detail": "Conversation not found"
}
```

**Behavior**:
- Verify user ownership
- Delete conversation (cascade delete messages)
- Return 204 No Content
- Return 404 if not found or not owned

---

## Error Handling

### Standard Error Response Format

All error responses follow this format:

```json
{
  "detail": "User-friendly error message"
}
```

### Status Code Summary

| Status | Meaning | When Used |
|--------|---------|-----------|
| 200 | OK | Successful GET or message send |
| 201 | Created | (Not used in chat API) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request (empty message, etc.) |
| 401 | Unauthorized | JWT missing/invalid or ownership violation |
| 404 | Not Found | Conversation doesn't exist or not owned |
| 429 | Too Many Requests | Rate limit exceeded |
| 503 | Service Unavailable | OpenAI API down |

### User-Friendly Error Messages

**400 Bad Request**:
- Message is empty: "Message cannot be empty"
- Message too long: "Message must be under 10,000 characters"

**401 Unauthorized**:
- User ID mismatch: "User ID mismatch"
- Invalid JWT: "Invalid or expired token"
- Ownership violation: "User ID mismatch"

**404 Not Found**:
- Conversation not found: "Conversation not found" (no indication of ownership)

**429 Too Many Requests**:
- Rate limit exceeded: "Rate limit exceeded: max 20 requests per minute"

**503 Service Unavailable**:
- OpenAI API error: "Chat service temporarily unavailable"
- Database error: "Chat service temporarily unavailable"

### Error Handling Guidelines

1. **Never leak internal details** in error messages
2. **Use 404 for both "not found" and "not owned"** to prevent enumeration
3. **Log technical errors server-side** for debugging
4. **Return generic messages to clients** for security errors
5. **Include "detail" field in all error responses** for parsing

---

## Authentication

### JWT Token Format

Expected JWT structure:
```
Header: {
  "alg": "HS256",
  "typ": "JWT"
}

Payload: {
  "sub": "123",          // user_id
  "iat": 1708419750,    // issued at
  "exp": 1708506150     // expiration
}

Signature: [HMAC-SHA256]
```

### Token Usage

**In Requests**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Validation**:
- Verify signature using shared secret
- Check expiration (`exp` claim)
- Extract `sub` (user_id) claim
- Verify `sub` matches path parameter

### Rate Limiting

- **Limit**: 20 requests per minute per user
- **Tracking**: By user ID (from JWT)
- **Response**: 429 with message

---

## Integration Checklist

**Frontend**:
- [ ] Install `@openai/chatkit` dependency
- [ ] Create `chat-client.ts` with all 4 endpoints
- [ ] Create `ChatContainer.tsx` component
- [ ] Handle all error status codes
- [ ] Include JWT in Authorization header
- [ ] Extract user_id from JWT token
- [ ] Display user-friendly error messages
- [ ] Implement retry logic for transient errors

**Backend**:
- [ ] Implement `POST /api/{user_id}/chat` endpoint
- [ ] Implement `GET /api/{user_id}/conversations` endpoint
- [ ] Implement `GET /api/{user_id}/conversations/{id}` endpoint
- [ ] Implement `DELETE /api/{user_id}/conversations/{id}` endpoint
- [ ] Validate JWT on all endpoints
- [ ] Enforce rate limiting (20 req/min per user)
- [ ] Store messages in database
- [ ] Integrate with OpenAI Agent SDK
- [ ] Return proper error codes and messages

---

## Examples

### Example 1: First Message (New Conversation)

```bash
# Request
POST /api/123/chat HTTP/1.1
Authorization: Bearer eyJ...
Content-Type: application/json

{
  "conversation_id": null,
  "message": "What is this app about?"
}

# Response (200 OK)
{
  "message_id": 50,
  "conversation_id": 10,
  "role": "assistant",
  "content": "This is a task management app with AI assistance. You can create, organize, and manage your tasks. I can help you with suggestions, prioritization, and more.",
  "timestamp": "2026-02-20T14:00:00Z"
}
```

### Example 2: Follow-up Message (Existing Conversation)

```bash
# Request
POST /api/123/chat HTTP/1.1
Authorization: Bearer eyJ...
Content-Type: application/json

{
  "conversation_id": 10,
  "message": "Can you help me create a new task?"
}

# Response (200 OK)
{
  "message_id": 51,
  "conversation_id": 10,
  "role": "assistant",
  "content": "Of course! To create a new task, I can help you:\n1. Define the task name and description\n2. Set a priority level\n3. Optionally add a due date\n\nWhat would you like the task to be about?",
  "timestamp": "2026-02-20T14:02:00Z"
}
```

### Example 3: Rate Limit Error

```bash
# Request (21st request within 1 minute)
POST /api/123/chat HTTP/1.1
Authorization: Bearer eyJ...
Content-Type: application/json

{
  "conversation_id": 10,
  "message": "One more question"
}

# Response (429 Too Many Requests)
{
  "detail": "Rate limit exceeded: max 20 requests per minute"
}
```

### Example 4: Ownership Violation

```bash
# Request (user 456 trying to access user 123's conversation)
GET /api/456/conversations/10 HTTP/1.1
Authorization: Bearer eyJ.sub.456...

# Response (404 Not Found - no info leakage)
{
  "detail": "Conversation not found"
}
```

---

## Version History

**v1.0.0** (2026-02-20)
- Initial API contract definition
- Covers send message, list conversations, get details, delete
- JWT authentication required
- Rate limiting at 20 req/min per user