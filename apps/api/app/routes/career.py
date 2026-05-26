"""
Career Chat Route
Endpoint for recruiters to ask AI questions about Srikanth's background.
"""

import asyncio
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from apps.api.app.agents.career_agent import run_career_agent


router = APIRouter(prefix="/career", tags=["career"])


class CareerChatRequest(BaseModel):
    """Request to chat with the career agent."""
    message: str
    session_id: Optional[str] = None


class CareerChatResponse(BaseModel):
    """Response from the career agent."""
    response: str
    tools_used: list[str]
    iterations: int
    response_time_ms: float


@router.post("/chat", response_model=CareerChatResponse)
async def career_chat(request: CareerChatRequest) -> CareerChatResponse:
    """
    Chat with the AI assistant about Srikanth's background.

    Args:
        request: Chat request with message and optional session_id

    Returns:
        Chat response with AI answer and metadata
    """
    if not request.message or len(request.message.strip()) == 0:
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    start_time = time.perf_counter()

    try:
        result = await asyncio.wait_for(
            run_career_agent(request.message),
            timeout=120.0
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return CareerChatResponse(
            response=result["response"],
            tools_used=result["tools_used"],
            iterations=result["iterations"],
            response_time_ms=round(elapsed_ms, 2)
        )

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timed out after 60 seconds")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/health")
async def career_health():
    """Health check for career service."""
    return {
        "status": "ok",
        "service": "career-agent"
    }
