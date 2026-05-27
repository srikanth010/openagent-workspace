"""
Career Chat Route
Endpoint for recruiters to ask AI questions about Srikanth's background.
"""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from apps.api.app.agents.career_agent import run_career_agent, CareerAgent
from apps.api.app.core import session_store


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
    context_preview: Optional[str] = None


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
            response_time_ms=round(elapsed_ms, 2),
            context_preview=result.get("context_preview"),
        )

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timed out after 60 seconds")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.websocket("/ws")
async def career_ws(websocket: WebSocket):
    """
    WebSocket endpoint for streaming career chat with conversation memory.

    Client sends: {"message": "...", "session_id": "..."}
    Server streams: {"token": "..."} then {"done": true, "tools_used": [...]}
    """
    await websocket.accept()

    try:
        while True:
            # Receive message from client
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
                continue

            message = data.get("message", "").strip()
            session_id = data.get("session_id", "").strip()

            if not message:
                await websocket.send_json({"error": "Message cannot be empty"})
                continue

            if not session_id:
                session_id = str(uuid.uuid4())

            # Evict stale sessions and get history
            session_store.evict_stale(ttl_seconds=1800)
            history = session_store.get_history(session_id, limit=10)

            # Stream the response
            agent = CareerAgent()
            full_response = ""
            tools_used = []

            try:
                async for chunk in agent.run_streaming(message, history):
                    if "token" in chunk:
                        token = chunk["token"]
                        full_response += token
                        await websocket.send_json({"token": token})
                    elif chunk.get("done"):
                        tools_used = chunk.get("tools_used", [])
                        await websocket.send_json({
                            "done": True,
                            "tools_used": tools_used,
                            "session_id": session_id
                        })

                # Save the exchange to session history
                session_store.append_turn(session_id, "user", message)
                session_store.append_turn(session_id, "assistant", full_response)

            except asyncio.TimeoutError:
                await websocket.send_json({"error": "Request timed out"})
            except Exception as e:
                await websocket.send_json({"error": f"Internal error: {str(e)}"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": f"WebSocket error: {str(e)}"})
        except Exception:
            pass


@router.get("/health")
async def career_health():
    """Health check for career service."""
    return {
        "status": "ok",
        "service": "career-agent"
    }


@router.get("/debug/paths")
async def career_debug_paths():
    """Debug endpoint to check file paths on the server."""
    import os
    mcp_server = Path(__file__).resolve().parent.parent.parent.parent / "mcp" / "career_server.py"
    root_from_mcp = mcp_server.resolve().parents[2] if mcp_server.exists() else None
    data_dir = root_from_mcp / "data" if root_from_mcp else None
    return {
        "cwd": os.getcwd(),
        "this_file": str(Path(__file__).resolve()),
        "mcp_server_path": str(mcp_server),
        "mcp_server_exists": mcp_server.exists(),
        "data_dir": str(data_dir) if data_dir else None,
        "career_yaml_exists": (data_dir / "career.yaml").exists() if data_dir else False,
        "projects_yaml_exists": (data_dir / "projects.yaml").exists() if data_dir else False,
        "data_dir_listing": os.listdir(str(data_dir)) if data_dir and data_dir.exists() else [],
    }
