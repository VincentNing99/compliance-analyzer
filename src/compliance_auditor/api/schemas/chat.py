"""Pydantic schemas for chat endpoints."""
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str                              # The user's message
    chat_history: list[ChatMessage] = []      # Previous messages for context
    selected_compliance: list[str] = []       # Selected compliance doc IDs
    selected_internal: list[str] = []         # Selected internal doc IDs
