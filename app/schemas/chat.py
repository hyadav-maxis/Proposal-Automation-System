"""Pydantic schemas for the AI chat endpoint."""

from typing import Dict, List
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single message in a conversation."""

    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    """Request body for the /api/chat endpoint."""

    messages: List[Dict[str, str]]
