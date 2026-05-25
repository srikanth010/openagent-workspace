from fastapi import APIRouter
from pydantic import BaseModel

from apps.api.app.agents.chat_agent import run_chat_agent

router = APIRouter(prefix="/agent", tags=["Agent"])

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
def chat(request: ChatRequest):
    response = run_chat_agent(request.message)

    return {
        "input": request.message,
        "response": response,
    }
