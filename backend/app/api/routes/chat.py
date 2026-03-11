"""Chat endpoint routes for AI chatbot (Spec-4).

Provides:
- POST /api/{user_id}/chat - Send message to chatbot
- GET /api/{user_id}/conversations - List user's conversations
- GET /api/{user_id}/conversations/{id} - Get conversation with messages
- DELETE /api/{user_id}/conversations/{id} - Delete conversation
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.deps import get_current_user, get_db
from app.models.conversation import Conversation, Message
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api", tags=["chat"])

# Global chat service instance (stateless, no session stored)
chat_service = ChatService()


class ChatRequest(BaseModel):
    """Request model for sending chat message."""
    conversation_id: Optional[int] = None
    message: str


class ChatResponse(BaseModel):
    """Response model for chat message."""
    message_id: int
    conversation_id: int
    role: str
    content: str
    timestamp: datetime


class MessageResponse(BaseModel):
    """Response model for a single message."""
    id: int
    role: str
    content: str
    timestamp: datetime


class ConversationDetail(BaseModel):
    """Response model for conversation with messages."""
    id: int
    title: Optional[str]
    created_at: datetime
    messages: list[MessageResponse]


class ConversationSummary(BaseModel):
    """Response model for conversation list."""
    id: int
    title: Optional[str]
    created_at: datetime
    message_count: int


@router.post("/{user_id}/chat", response_model=ChatResponse)
def send_chat_message(
    user_id: str,
    request: ChatRequest,
    current_user_id: int = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> ChatResponse:
    """
    Send message to AI chatbot.

    Spec-4 FR-001, FR-002, FR-003, FR-009, FR-010

    Flow:
    1. Verify JWT user matches path user
    2. Check rate limit
    3. Get/create conversation
    4. Store user message
    5. Call OpenAI Agent with conversation history
    6. Store agent response
    7. Return response

    Args:
        user_id: User ID from path
        request: Chat request with message
        current_user_id: Authenticated user ID from JWT
        session: Database session

    Returns:
        ChatResponse with message ID, role, content, timestamp

    Raises:
        HTTPException: 401 if JWT user doesn't match path user
        HTTPException: 429 if rate limit exceeded
        HTTPException: 503 if OpenAI API unavailable
    """
    # Verify JWT user matches path parameter (Principle VII)
    if str(current_user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID mismatch",
        )

    # Check rate limit (FR-011)
    if not chat_service.check_rate_limit(user_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded: max 20 requests per minute",
        )

    # Validate message (FR-001)
    if not request.message or len(request.message.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty",
        )

    try:
        # Get or create conversation (FR-003, FR-015)
        conversation = chat_service.get_or_create_conversation(
            session, user_id, request.conversation_id
        )

        # Store user message (FR-003)
        user_msg = chat_service.store_message(
            session,
            conversation.id,
            user_id,
            role="user",
            content=request.message,
        )

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

        # Return response (FR-009)
        return ChatResponse(
            message_id=assistant_msg.id,
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_msg.content,
            timestamp=assistant_msg.created_at,
        )

    except ValueError as e:
        # Conversation not found or not owned
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        # OpenAI API or database errors
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service temporarily unavailable",
        )


@router.get("/{user_id}/conversations", response_model=list[ConversationSummary])
def list_conversations(
    user_id: str,
    current_user_id: int = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[ConversationSummary]:
    """
    List all conversations for authenticated user.

    Spec-4 FR-013, FR-014

    Args:
        user_id: User ID from path
        current_user_id: Authenticated user ID from JWT
        session: Database session

    Returns:
        List of conversation summaries

    Raises:
        HTTPException: 401 if JWT user doesn't match path user
    """
    # Verify JWT user matches path parameter
    if str(current_user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID mismatch",
        )

    # Query conversations for user
    statement = select(Conversation).where(
        Conversation.user_id == user_id
    ).order_by(Conversation.created_at.desc())

    conversations = session.exec(statement).all()

    # Count messages for each conversation
    result = []
    for conv in conversations:
        msg_statement = select(Message).where(
            Message.conversation_id == conv.id
        )
        message_count = len(session.exec(msg_statement).all())

        result.append(
            ConversationSummary(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                message_count=message_count,
            )
        )

    return result


@router.get("/{user_id}/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    user_id: str,
    conversation_id: int,
    current_user_id: int = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> ConversationDetail:
    """
    Get conversation with all messages.

    Spec-4 FR-013, FR-014

    Args:
        user_id: User ID from path
        conversation_id: Conversation ID
        current_user_id: Authenticated user ID from JWT
        session: Database session

    Returns:
        Conversation with messages

    Raises:
        HTTPException: 401 if JWT user doesn't match path user
        HTTPException: 404 if conversation not found or not owned
    """
    # Verify JWT user matches path parameter
    if str(current_user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID mismatch",
        )

    # Get conversation
    statement = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id,
    )
    conversation = session.exec(statement).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Get messages
    msg_statement = select(Message).where(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at)

    messages = session.exec(msg_statement).all()

    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        messages=[
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.created_at,
            )
            for msg in messages
        ],
    )


@router.delete("/{user_id}/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    user_id: str,
    conversation_id: int,
    current_user_id: int = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Response:
    """
    Delete conversation and all messages.

    Spec-4 FR-013, FR-014

    Args:
        user_id: User ID from path
        conversation_id: Conversation ID
        current_user_id: Authenticated user ID from JWT
        session: Database session

    Returns:
        204 No Content

    Raises:
        HTTPException: 401 if JWT user doesn't match path user
        HTTPException: 404 if conversation not found or not owned
    """
    # Verify JWT user matches path parameter
    if str(current_user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID mismatch",
        )

    # Get conversation
    statement = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id,
    )
    conversation = session.exec(statement).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Delete conversation (cascade deletes messages)
    session.delete(conversation)
    session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
