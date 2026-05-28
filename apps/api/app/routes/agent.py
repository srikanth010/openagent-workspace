from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import uuid

from apps.api.app.agents.chat_agent import run_chat_agent
from apps.api.app.core import session_store

router = APIRouter(prefix="/agent", tags=["Agent"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/chat")
def chat(request: ChatRequest):
    session_store.evict_stale(ttl_seconds=1800)
    session_id = request.session_id.strip() if request.session_id else str(uuid.uuid4())
    history = session_store.get_history(session_id, limit=10)

    response = run_chat_agent(request.message, history=history)

    session_store.append_turn(session_id, "user", request.message)
    session_store.append_turn(session_id, "assistant", response)

    return {
        "input": request.message,
        "response": response,
        "session_id": session_id,
    }
