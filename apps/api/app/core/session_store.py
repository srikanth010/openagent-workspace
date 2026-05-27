"""
In-memory session store for conversation history.
Sessions auto-expire after TTL and are lost on server restart.
"""

import time
from typing import Optional


class Session:
    """A conversation session with history and last activity timestamp."""

    def __init__(self):
        self.messages: list[dict] = []
        self.last_active = time.time()

    def add_message(self, role: str, content: str):
        """Add a message to the session history."""
        self.messages.append({"role": role, "content": content})
        self.last_active = time.time()

    def get_history(self, limit: int = 10) -> list[dict]:
        """Get conversation history, capped at limit (to fit context window)."""
        if len(self.messages) > limit:
            return self.messages[-limit:]
        return self.messages

    def is_stale(self, ttl_seconds: int) -> bool:
        """Check if session has exceeded TTL."""
        return time.time() - self.last_active > ttl_seconds


# Global session store
_sessions: dict[str, Session] = {}


def get_or_create_session(session_id: str) -> Session:
    """Get an existing session or create a new one."""
    if session_id not in _sessions:
        _sessions[session_id] = Session()
    else:
        _sessions[session_id].last_active = time.time()
    return _sessions[session_id]


def get_history(session_id: str, limit: int = 10) -> list[dict]:
    """Get conversation history for a session."""
    if session_id not in _sessions:
        return []
    return _sessions[session_id].get_history(limit)


def append_turn(session_id: str, role: str, content: str):
    """Add a turn (user or assistant message) to the session."""
    session = get_or_create_session(session_id)
    session.add_message(role, content)


def evict_stale(ttl_seconds: int = 1800) -> int:
    """
    Remove sessions that haven't been active for TTL.
    Returns the number of sessions evicted.
    """
    global _sessions
    stale_ids = [
        sid for sid, session in _sessions.items()
        if session.is_stale(ttl_seconds)
    ]
    for sid in stale_ids:
        del _sessions[sid]
    return len(stale_ids)


def clear():
    """Clear all sessions (for testing)."""
    global _sessions
    _sessions.clear()
