"""Conversation and Message SQLModel definitions for AI chatbot (Spec-4).

Models:
- Conversation: Chat conversation entity with user ownership
- Message: Individual message in a conversation
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Conversation(SQLModel, table=True):
    """
    Conversation entity for AI chatbot.

    Ownership: Each conversation belongs to exactly one user via user_id.
    All queries MUST filter by user_id (Constitution XIX).
    """
    __tablename__ = "conversation"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, nullable=False)
    title: Optional[str] = Field(max_length=255, default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    """
    Message entity for conversations.

    Role: "user" or "assistant"
    Denormalized user_id for security verification (Principle XIX).
    """
    __tablename__ = "message"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", nullable=False)
    user_id: str = Field(index=True, nullable=False)
    role: str = Field(default="user", max_length=20)  # "user" or "assistant"
    content: str = Field()
    created_at: datetime = Field(default_factory=datetime.utcnow)
