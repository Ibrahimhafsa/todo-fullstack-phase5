"""Chat service layer for AI chatbot functionality (Spec-4).

Handles:
- Message storage (user + assistant)
- Rate limiting (per user, per minute)
- Conversation history retrieval
- OpenAI Agent integration with MCP tools
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import json
import logging

from openai import OpenAI, APIError, APITimeoutError
from sqlmodel import Session, select

from app.config import settings
from app.models.conversation import Conversation, Message
from app.api.mcp_server.server import MCPToolRegistry

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Per-user rate limiting.

    Tracks requests per user per minute.
    Stateless: counter reset on minute boundary.
    """

    def __init__(self, max_requests_per_minute: int = 20):
        """Initialize rate limiter."""
        self.max_requests = max_requests_per_minute
        # In-memory counter: {user_id: (count, minute_timestamp)}
        self._counters: Dict[str, tuple[int, datetime]] = {}

    def check_and_increment(self, user_id: str) -> bool:
        """
        Check if user is within rate limit and increment counter.

        Returns:
            True if request allowed, False if rate limit exceeded
        """
        now = datetime.utcnow()
        current_minute = now.replace(second=0, microsecond=0)

        if user_id not in self._counters:
            self._counters[user_id] = (1, current_minute)
            return True

        count, minute_timestamp = self._counters[user_id]

        # Check if we're in a new minute
        if minute_timestamp < current_minute:
            # Reset counter for new minute
            self._counters[user_id] = (1, current_minute)
            return True

        # Same minute - check if under limit
        if count < self.max_requests:
            self._counters[user_id] = (count + 1, minute_timestamp)
            return True

        # Rate limit exceeded
        return False


class ChatService:
    """Service layer for chat operations."""

    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        """Initialize chat service."""
        self.rate_limiter = rate_limiter or RateLimiter()

    def check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user is within rate limit.

        Returns:
            True if allowed, False if rate limit exceeded
        """
        return self.rate_limiter.check_and_increment(user_id)

    def get_or_create_conversation(
        self,
        session: Session,
        user_id: str,
        conversation_id: Optional[int] = None,
    ) -> Conversation:
        """
        Get existing conversation or create new one.

        Args:
            session: Database session
            user_id: Authenticated user ID from JWT
            conversation_id: Existing conversation ID or None for new

        Returns:
            Conversation instance

        Raises:
            ValueError: If conversation_id not owned by user
        """
        if conversation_id is None:
            # Create new conversation
            conversation = Conversation(user_id=user_id)
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            return conversation

        # Get existing conversation
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        conversation = session.exec(statement).first()

        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found or not owned by user")

        return conversation

    def store_message(
        self,
        session: Session,
        conversation_id: int,
        user_id: str,
        role: str,
        content: str,
    ) -> Message:
        """
        Store message in database.

        Args:
            session: Database session
            conversation_id: Conversation ID
            user_id: User ID (denormalized for security verification)
            role: "user" or "assistant"
            content: Message content

        Returns:
            Stored Message instance
        """
        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content,
        )
        session.add(message)
        session.commit()
        session.refresh(message)
        return message

    def get_conversation_history(
        self,
        session: Session,
        conversation_id: int,
        user_id: str,
    ) -> list[Message]:
        """
        Get all messages in conversation.

        Args:
            session: Database session
            conversation_id: Conversation ID
            user_id: User ID (for ownership verification)

        Returns:
            List of Message instances in chronological order
        """
        statement = select(Message).where(
            Message.conversation_id == conversation_id,
            Message.user_id == user_id,
        ).order_by(Message.created_at)

        return list(session.exec(statement).all())

    def send_message(
        self,
        session: Session,
        user_id: str,
        conversation_id: Optional[int],
        message_text: str,
    ) -> tuple[Message, Optional[str]]:
        """
        Process user message through OpenAI Agent with MCP tools.

        Flow:
        1. Get or create conversation
        2. Store user message
        3. Load conversation history
        4. Initialize OpenAI Client
        5. Build MCP tool registry
        6. Call agent with message + history + tools
        7. Execute any tool calls
        8. Store agent response
        9. Return response

        Args:
            session: Database session
            user_id: Authenticated user ID from JWT
            conversation_id: Existing conversation or None for new
            message_text: User message content

        Returns:
            Tuple of (response_message, error_message)
            - response_message: Stored Message instance with assistant response
            - error_message: None if success, error detail if failure

        Raises:
            ValueError: If conversation not owned by user
        """
        try:
            # Get or create conversation
            conversation = self.get_or_create_conversation(
                session, user_id, conversation_id
            )

            # Store user message
            user_msg = self.store_message(
                session,
                conversation.id,
                user_id,
                role="user",
                content=message_text,
            )

            # Get conversation history for agent context
            history = self.get_conversation_history(
                session, conversation.id, user_id
            )

            # Create MCP tool registry (stateless per request)
            mcp_registry = MCPToolRegistry(session)

            # Initialize OpenAI client
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            # Convert history to OpenAI message format
            messages = self._build_message_history(history, message_text)

            # Build system prompt with MCP tool guidance
            system_prompt = self._build_system_prompt()

            # Build tools list for OpenAI API
            tools_list = self._build_tools_list(mcp_registry)

            # Call OpenAI with tools (3 retry attempts with backoff)
            agent_response = self._call_openai_with_retry(
                client, messages, system_prompt, tools_list, mcp_registry, user_id
            )

            # Store assistant response
            assistant_msg = self.store_message(
                session,
                conversation.id,
                user_id,
                role="assistant",
                content=agent_response,
            )

            logger.info(
                f"Chat message processed: user={user_id}, conversation={conversation.id}, "
                f"message_id={user_msg.id}, response_id={assistant_msg.id}"
            )

            return assistant_msg, None

        except ValueError as e:
            # Conversation ownership error
            logger.warning(f"Conversation error for user {user_id}: {str(e)}")
            raise
        except (APIError, APITimeoutError) as e:
            # OpenAI API error
            logger.error(f"OpenAI API error for user {user_id}: {str(e)}")
            return None, "AI service temporarily unavailable"
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error in send_message for user {user_id}: {str(e)}")
            return None, "Chat service error"

    def _build_message_history(
        self, history: list[Message], new_message: str
    ) -> list[Dict[str, str]]:
        """
        Convert database messages to OpenAI format.

        Args:
            history: List of Message instances (excluding latest user message)
            new_message: Latest user message to append

        Returns:
            List of messages in OpenAI format: [{"role": "...", "content": "..."}]
        """
        messages = []

        # Add previous history
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})

        # Add latest user message
        messages.append({"role": "user", "content": new_message})

        return messages

    def _build_system_prompt(self) -> str:
        """
        Build system prompt for agent.

        Guides agent to use MCP tools for task operations.

        Returns:
            System prompt string
        """
        return """You are a helpful task management assistant. Your goal is to help users manage their tasks through natural language.

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

    def _build_tools_list(self, mcp_registry: "MCPToolRegistry") -> list[Dict[str, Any]]:
        """
        Build OpenAI tools list from MCP registry.

        Args:
            mcp_registry: MCPToolRegistry instance

        Returns:
            List of tool definitions for OpenAI API
        """
        tools = []
        for tool_name, tool_schema in mcp_registry.get_tool_schemas().items():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_schema["name"],
                    "description": tool_schema["description"],
                    "parameters": tool_schema["parameters"],
                },
            })
        return tools

    def _call_openai_with_retry(
        self,
        client: OpenAI,
        messages: list[Dict[str, str]],
        system_prompt: str,
        tools: list[Dict[str, Any]],
        mcp_registry: "MCPToolRegistry",
        user_id: str,
        max_retries: int = 3,
    ) -> str:
        """
        Call OpenAI with tool support and retry logic.

        Flow:
        1. Call OpenAI API with tools
        2. If response includes tool_calls:
           - Execute each tool call via MCP registry
           - Append results to messages
           - Call OpenAI again with results
        3. Return final text response

        Args:
            client: OpenAI client
            messages: Message history
            system_prompt: System prompt
            tools: Tools list for OpenAI
            mcp_registry: MCP tool registry
            user_id: User ID for tool calls
            max_retries: Max retry attempts on timeout

        Returns:
            Final assistant response text

        Raises:
            APIError: If OpenAI API fails after retries
            APITimeoutError: If request times out
        """
        import time

        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                # Call OpenAI with tools
                response = client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *messages,
                    ],
                    tools=tools,
                    timeout=settings.OPENAI_TIMEOUT,
                )

                # Process response
                assistant_message = response.choices[0].message

                # Handle tool calls
                if assistant_message.tool_calls:
                    # Execute tools and collect results
                    tool_results = self._execute_tool_calls(
                        assistant_message.tool_calls, mcp_registry, user_id
                    )

                    # Add assistant message with tool calls
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message.content or "",
                        "tool_calls": [
                            {
                                "id": call.id,
                                "type": "function",
                                "function": {
                                    "name": call.function.name,
                                    "arguments": call.function.arguments,
                                },
                            }
                            for call in assistant_message.tool_calls
                        ],
                    })

                    # Add tool results as proper tool messages
                    for tool_result in tool_results:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_result["tool_call_id"],
                            "content": tool_result["content"],
                        })

                    # Call OpenAI again with results
                    response = client.chat.completions.create(
                        model=settings.OPENAI_MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            *messages,
                        ],
                        tools=tools,
                        timeout=settings.OPENAI_TIMEOUT,
                    )

                    assistant_message = response.choices[0].message

                # Return final text response
                return assistant_message.content or "I've processed your request."

            except APITimeoutError as e:
                last_error = e
                retry_count += 1
                if retry_count < max_retries:
                    # Exponential backoff
                    wait_time = 2 ** retry_count
                    logger.warning(
                        f"OpenAI timeout for user {user_id}, retry {retry_count}/{max_retries} "
                        f"after {wait_time}s"
                    )
                    time.sleep(wait_time)
                else:
                    raise

        # All retries exhausted
        raise last_error or APITimeoutError("OpenAI request timeout")

    def _execute_tool_calls(
        self,
        tool_calls: list[Any],
        mcp_registry: "MCPToolRegistry",
        user_id: str,
    ) -> list[Dict[str, Any]]:
        """
        Execute tool calls and return results.

        Args:
            tool_calls: List of tool calls from OpenAI
            mcp_registry: MCP tool registry
            user_id: User ID for tool parameter

        Returns:
            List of tool result dicts with tool_call_id and content
        """
        results = []

        for tool_call in tool_calls:
            try:
                # Parse tool arguments
                tool_args = json.loads(tool_call.function.arguments)

                # Add user_id to all tool calls (from JWT context)
                tool_args["user_id"] = user_id

                # Execute tool
                tool_name = tool_call.function.name
                tool_result = mcp_registry.call_tool(tool_name, **tool_args)

                # Format result for OpenAI tool message
                result_dict = {
                    "tool_call_id": tool_call.id,
                    "content": json.dumps({
                        "tool_name": tool_name,
                        "result": tool_result,
                        "success": True,
                    }),
                }

                results.append(result_dict)

                logger.debug(
                    f"Tool executed: user={user_id}, tool={tool_name}, result_keys={list(tool_result.keys()) if isinstance(tool_result, dict) else 'N/A'}"
                )

            except json.JSONDecodeError as e:
                # Failed to parse arguments
                result_dict = {
                    "tool_call_id": tool_call.id,
                    "content": json.dumps({
                        "tool_name": tool_call.function.name,
                        "error": f"Invalid arguments: {str(e)}",
                        "success": False,
                    }),
                }
                results.append(result_dict)
                logger.error(f"Failed to parse tool arguments: {str(e)}")

            except Exception as e:
                # Tool execution failed
                result_dict = {
                    "tool_call_id": tool_call.id,
                    "content": json.dumps({
                        "tool_name": tool_call.function.name,
                        "error": str(e),
                        "success": False,
                    }),
                }
                results.append(result_dict)
                logger.error(f"Tool execution error: {str(e)}")

        return results
