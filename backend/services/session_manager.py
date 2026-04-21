"""
Session Manager - Handles chat conversation persistence and history
"""
from typing import Dict, List, Optional
from datetime import datetime
import uuid
from schemas.chat_models import ChatMessage


class ChatSession:
    """Represents a single chat conversation session"""

    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.messages: List[ChatMessage] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.title = "New Conversation"

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation"""
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat()
        )
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

        # Auto-generate title from first user message
        if role == "user" and len(self.messages) == 1:
            self.title = content[:50] + ("..." if len(content) > 50 else "")

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Get conversation history in Claude API format"""
        messages = self.messages[-limit:] if limit else self.messages
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    def to_dict(self) -> Dict:
        """Convert session to dictionary for API responses"""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "message_count": len(self.messages),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp
                }
                for msg in self.messages
            ]
        }


class SessionManager:
    """Manages multiple chat sessions in memory"""

    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        print("✓ Session Manager initialized")

    def create_session(self) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession()
        self.sessions[session.session_id] = session
        print(f"[Session] Created new session: {session.session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get an existing session by ID"""
        return self.sessions.get(session_id)

    def get_or_create_session(self, session_id: Optional[str] = None) -> ChatSession:
        """Get existing session or create new one"""
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        return self.create_session()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            print(f"[Session] Deleted session: {session_id}")
            return True
        return False

    def list_sessions(self, limit: int = 20) -> List[Dict]:
        """List all sessions (most recent first)"""
        sessions = sorted(
            self.sessions.values(),
            key=lambda s: s.updated_at,
            reverse=True
        )[:limit]

        return [
            {
                "session_id": s.session_id,
                "title": s.title,
                "message_count": len(s.messages),
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat()
            }
            for s in sessions
        ]

    def clear_old_sessions(self, max_age_hours: int = 24):
        """Clear sessions older than specified hours"""
        now = datetime.utcnow()
        to_delete = []

        for session_id, session in self.sessions.items():
            age_hours = (now - session.updated_at).total_seconds() / 3600
            if age_hours > max_age_hours:
                to_delete.append(session_id)

        for session_id in to_delete:
            del self.sessions[session_id]

        if to_delete:
            print(f"[Session] Cleared {len(to_delete)} old sessions")


# Singleton instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get or create the session manager singleton"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
