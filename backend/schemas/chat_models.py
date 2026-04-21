"""
Pydantic models for chat functionality
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single chat message"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Request payload for chat endpoint"""
    message: str
    session_id: Optional[str] = None  # Session ID for conversation continuity
    conversation_history: List[ChatMessage] = []  # Deprecated: now managed server-side
    filters: Optional[Dict[str, Any]] = {}  # Additional filters for queries


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    response: str
    suggestions: List[str]
    session_id: Optional[str] = None  # Session ID to use for follow-up messages
    data: Optional[Dict[str, Any]] = None
    chart_type: Optional[str] = None
    function_calls: Optional[List[str]] = []  # Show which functions were called


class ToolResult(BaseModel):
    """Result from a tool/function call"""
    tool_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
