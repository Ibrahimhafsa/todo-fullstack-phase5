# OpenAI Agent + MCP Tool Integration Guide

**What Changed**: Mock assistant response → Real OpenAI Agent with MCP tools

---

## Before (Mock Response)

```python
# backend/app/api/routes/chat.py:145-147
# TODO (Phase 3): Call OpenAI Agents SDK with MCP tools
# For MVP: Create mock response (will be replaced with agent call)
agent_response = f"Received message: {request.message[:50]}"
```

**Result**: Endpoint always returned mock response, no task operations performed

---

## After (Real Agent)

```python
# backend/app/api/routes/chat.py:145-158
# Call OpenAI Agent with MCP tools (FR-005, FR-006, FR-007, FR-008)
assistant_msg, error = chat_service.send_message(
    session,
    user_id,
    conversation.id,
    request.message,
)

# Handle OpenAI API errors
if error:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=error,
    )
```

**Result**: Agent processes natural language, calls MCP tools, performs actual task operations, returns intelligent response

---

## How It Works

### 1. User sends message
```json
POST /api/123/chat
{
  "message": "Create a task called 'Buy groceries'"
}
```

### 2. Endpoint calls ChatService.send_message()
```python
# Stateless per-request flow
assistant_msg, error = chat_service.send_message(
    session,           # DB session for persistence
    user_id="123",     # From JWT authentication
    conversation_id=None,  # New conversation
    message_text="Create a task called 'Buy groceries'"
)
```

### 3. Service orchestrates agent workflow

**Step A: Setup**
```python
# Get/create conversation
conversation = self.get_or_create_conversation(session, user_id, conversation_id)

# Store user message
user_msg = self.store_message(session, conversation.id, user_id, "user", message_text)

# Load history for context
history = self.get_conversation_history(session, conversation.id, user_id)
```

**Step B: Initialize Agent**
```python
# Create MCP tool registry
mcp_registry = MCPToolRegistry(session)

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Convert history to OpenAI format
messages = self._build_message_history(history, message_text)

# Build system prompt
system_prompt = self._build_system_prompt()

# Build tools list
tools_list = self._build_tools_list(mcp_registry)
```

**Step C: Call Agent with Retry Logic**
```python
# Try up to 3 times with exponential backoff on timeout
agent_response = self._call_openai_with_retry(
    client, 
    messages, 
    system_prompt, 
    tools_list, 
    mcp_registry, 
    user_id,
    max_retries=3
)
```

**Step D: Handle Tool Calls**
If agent decides to call a tool:
```python
# 1. Parse tool arguments
tool_args = json.loads(tool_call.function.arguments)

# 2. Inject user context
tool_args["user_id"] = user_id

# 3. Execute via MCP registry (delegates to task_service)
tool_result = mcp_registry.call_tool(tool_name, **tool_args)

# 4. Return result to agent
# 5. Agent generates natural language response
```

**Step E: Store Response**
```python
# Save assistant response to database
assistant_msg = self.store_message(
    session,
    conversation.id,
    user_id,
    "assistant",
    agent_response
)
```

### 4. Return Response to Client
```json
200 OK
{
  "message_id": 42,
  "conversation_id": 1,
  "role": "assistant",
  "content": "Task 'Buy groceries' has been created.",
  "timestamp": "2026-02-19T10:30:00Z"
}
```

### 5. Full Conversation History Persisted
```sql
-- conversation table
| id | user_id | title | created_at |
| 1  | 123     | NULL  | 2026-02-19 |

-- message table
| id | conversation_id | user_id | role      | content                              | created_at |
| 1  | 1               | 123     | user      | "Create a task called 'Buy groceries'" | 2026-02-19 |
| 2  | 1               | 123     | assistant | "Task 'Buy groceries' has been created." | 2026-02-19 |
```

---

## MCP Tools Available to Agent

The agent can use these 6 tools (all delegate to Phase-2 task_service):

### 1. list_tasks
```python
# Get all user's tasks
mcp_registry.call_tool("list_tasks", user_id=user_id)
# Returns: [{"id": 1, "title": "Buy groceries", "is_complete": false, ...}, ...]
```

### 2. get_task
```python
# Get single task details
mcp_registry.call_tool("get_task", user_id=user_id, task_id=1)
# Returns: {"id": 1, "title": "Buy groceries", "description": "...", "is_complete": false}
```

### 3. create_task
```python
# Create new task
mcp_registry.call_tool("create_task", user_id=user_id, title="Buy groceries", description="Fresh produce")
# Returns: {"id": 1, "title": "Buy groceries", "description": "Fresh produce", "is_complete": false}
```

### 4. update_task
```python
# Update existing task
mcp_registry.call_tool("update_task", user_id=user_id, task_id=1, title="Buy vegetables")
# Returns: {"id": 1, "title": "Buy vegetables", ...}
```

### 5. delete_task
```python
# Delete task
mcp_registry.call_tool("delete_task", user_id=user_id, task_id=1)
# Returns: True
```

### 6. complete_task
```python
# Toggle task completion
mcp_registry.call_tool("complete_task", user_id=user_id, task_id=1)
# Returns: {"id": 1, "is_complete": true, ...}
```

---

## Agent Prompt Engineering

System prompt guides agent to recognize user intent and call appropriate tools:

```python
system_prompt = """You are a helpful task management assistant. Your goal is to help users manage their tasks through natural language.

When the user asks you to:
- Create, add, or remember a task → use create_task
- List, show, or see their tasks → use list_tasks
- Complete, finish, or mark done a task → use complete_task
- Delete, remove, or cancel a task → use delete_task
- Update, rename, or change a task → use update_task
- Get details about a specific task → use get_task

Always confirm actions with the user in a friendly way. For example:
- "Task 'Buy groceries' has been created."
- "I've marked 'Fix bug' as complete."
- "Your tasks have been deleted."

If a task cannot be found or an operation fails, ask the user for clarification.
Be concise and helpful."""
```

**Examples of Agent Behavior**:

| User Says | Agent Action | Agent Response |
|-----------|--------------|----------------|
| "Create a task called 'Buy groceries'" | Calls create_task("Buy groceries") | "Task 'Buy groceries' has been created." |
| "List my tasks" | Calls list_tasks() | "You have 3 tasks: Buy groceries, Fix bug, Call mom" |
| "Complete the first task" | Calls list_tasks(), then complete_task(1) | "I've marked 'Buy groceries' as complete." |
| "Delete all tasks" | Calls list_tasks(), then delete_task(1,2,3) | "I've deleted 3 tasks." |
| "What do I need to do?" | Calls list_tasks() | "You have 3 incomplete tasks: ..." |

---

## Error Handling

### OpenAI API Errors
```python
# Retry 3 times with exponential backoff (2s, 4s, 8s)
try:
    response = client.chat.completions.create(...)
except APITimeoutError:
    # Wait and retry
    time.sleep(2 ** retry_count)

# Return 503 to client if all retries fail
raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
```

### Tool Execution Errors
```python
# If tool fails (e.g., task not found):
try:
    result = mcp_registry.call_tool("complete_task", user_id=user_id, task_id=999)
except Exception as e:
    # Return error to agent
    return {"error": "Task not found", "success": False}

# Agent responds gracefully: "I couldn't find task 999. Would you like to see all your tasks?"
```

### Conversation Not Found
```python
# If user tries to access conversation they don't own:
conversation = self.get_or_create_conversation(session, user_id, conversation_id)
# Raises ValueError if not found or not owned

# Endpoint returns 404
raise HTTPException(status_code=404, detail="Conversation not found")
```

---

## Rate Limiting

Per-user limit: 20 requests per minute

```python
# Check before processing message
if not chat_service.check_rate_limit(user_id):
    raise HTTPException(
        status_code=429,
        detail="Rate limit exceeded: max 20 requests per minute"
    )
```

---

## Ownership Enforcement

All operations scoped to authenticated user:

```python
# 1. JWT extracts user_id
current_user_id = Depends(get_current_user)

# 2. Path user_id must match JWT
if str(current_user_id) != user_id:
    raise HTTPException(status_code=401, detail="User ID mismatch")

# 3. Conversation filtered by user_id
conversation = get_or_create_conversation(session, user_id)
# SQL: WHERE user_id = '{user_id}'

# 4. MCP tools receive user_id context
tool_args["user_id"] = user_id
# Task operations restricted to authenticated user

# 5. Response only contains user's data
# No cross-user data leaks
```

---

## Testing the Agent

### Manual Test (curl)
```bash
# 1. Get valid JWT token from /api/auth/signin
TOKEN=$(curl -X POST http://localhost:8000/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' | jq -r '.token')

# 2. Send message to agent
curl -X POST http://localhost:8000/api/123/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Create a task called 'Buy groceries'"}'

# Expected response:
# {
#   "message_id": 1,
#   "conversation_id": 1,
#   "role": "assistant",
#   "content": "Task 'Buy groceries' has been created.",
#   "timestamp": "2026-02-19T10:30:00Z"
# }

# 3. Verify task was created (Phase-2 endpoint)
curl -X GET http://localhost:8000/api/123/tasks \
  -H "Authorization: Bearer $TOKEN"

# Expected: Task 'Buy groceries' appears in response
```

### Integration Tests
```bash
cd backend
python -m pytest tests/integration/test_chat_endpoint.py -v

# Should pass:
# - test_send_message_creates_conversation
# - test_send_message_stores_user_message
# - test_send_message_stores_assistant_response
# - test_empty_message_returns_400
# - test_missing_jwt_returns_401
# - test_rate_limiting
# - test_list_conversations
# - test_get_conversation_detail
# - test_delete_conversation
# - test_ownership_enforcement
```

---

## Configuration

Set in `.env`:
```bash
# OpenAI API Key (required)
OPENAI_API_KEY=sk-...

# Model to use (default: gpt-4)
OPENAI_MODEL=gpt-4

# API timeout in seconds (default: 30)
OPENAI_TIMEOUT=30

# Rate limit: requests per minute per user (default: 20)
CHAT_RATE_LIMIT=20
```

---

## Architecture Diagram

```
User
  ↓
POST /api/{user_id}/chat (with JWT)
  ↓
FastAPI Endpoint (chat.py)
  ├─ Verify JWT
  ├─ Check rate limit
  ├─ Validate message
  └─ Call ChatService.send_message()
      ↓
  ChatService (chat_service.py)
  ├─ Get/create conversation
  ├─ Store user message in DB
  ├─ Load conversation history
  ├─ Initialize OpenAI Client
  ├─ Build MCP tool registry
  ├─ Call OpenAI API with tools (retry 3x)
  │   ├─ Agent receives message + history + tools
  │   ├─ Agent decides which tool to call
  │   ├─ Tool call executed via MCP registry
  │   │   └─ MCPToolRegistry
  │   │       ├─ list_tasks → task_service.list_tasks()
  │   │       ├─ get_task → task_service.get_task()
  │   │       ├─ create_task → task_service.create_task()
  │   │       ├─ update_task → task_service.update_task()
  │   │       ├─ delete_task → task_service.delete_task()
  │   │       └─ complete_task → task_service.toggle_complete()
  │   ├─ Agent receives tool result
  │   └─ Agent generates natural language response
  ├─ Store assistant response in DB
  └─ Return response to endpoint
      ↓
Return response to user (200 OK with message)
  ↓
User sees: "Task 'Buy groceries' has been created."
```

---

## Next Steps (Phase 4+)

1. **Phase 4 (US2)**: Add GET /api/{user_id}/conversations and GET /api/{user_id}/conversations/{id} to retrieve conversation history

2. **Phase 5 (US3)**: Enhance agent for bulk operations ("Complete all my tasks" → multiple tool calls)

3. **Phase 6 (US4)**: Frontend integration with isolated /chat route

4. **Phase 7**: Polish, security hardening, documentation, monitoring
