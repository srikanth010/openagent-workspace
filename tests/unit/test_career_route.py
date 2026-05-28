import asyncio

from apps.api.app.routes import career as career_route


async def _fake_run_career_agent(message, conversation_history=None):
    return {
        "response": f"answer:{message}",
        "tools_used": ["get_profile"],
        "iterations": 1,
        "context_preview": "ctx",
    }


def test_career_chat_success(client, monkeypatch):
    monkeypatch.setattr(career_route, "run_career_agent", _fake_run_career_agent)

    response = client.post("/career/chat", json={"message": "Tell me about skills", "session_id": "  s-1  "})

    assert response.status_code == 200
    payload = response.json()
    assert payload["response"] == "answer:Tell me about skills"
    assert payload["tools_used"] == ["get_profile"]
    assert payload["iterations"] == 1
    assert payload["session_id"] == "s-1"


def test_career_chat_empty_message_returns_422(client):
    response = client.post("/career/chat", json={"message": "   "})

    assert response.status_code == 422
    assert response.json()["detail"] == "Message cannot be empty"


def test_career_chat_timeout_returns_504(client, monkeypatch):
    async def _timeout_wait_for(*args, **kwargs):
        coro = args[0] if args else None
        if hasattr(coro, "close"):
            coro.close()
        raise asyncio.TimeoutError()

    monkeypatch.setattr(career_route, "run_career_agent", _fake_run_career_agent)
    monkeypatch.setattr(career_route.asyncio, "wait_for", _timeout_wait_for)

    response = client.post("/career/chat", json={"message": "hello"})

    assert response.status_code == 504


def test_career_health_route(client):
    response = client.get("/career/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "career-agent"}


def test_career_ws_streaming(client, monkeypatch):
    class FakeCareerAgent:
        async def run_streaming(self, message, history):
            yield {"token": "Hello"}
            yield {"token": " world"}
            yield {"done": True, "tools_used": ["list_skills"]}

    monkeypatch.setattr(career_route, "CareerAgent", FakeCareerAgent)

    with client.websocket_connect("/career/ws") as websocket:
        websocket.send_json({"message": "What are your skills?", "session_id": "session-a"})

        first = websocket.receive_json()
        second = websocket.receive_json()
        done = websocket.receive_json()

    assert first == {"token": "Hello"}
    assert second == {"token": " world"}
    assert done["done"] is True
    assert done["tools_used"] == ["list_skills"]
    assert done["session_id"] == "session-a"


def test_career_ws_invalid_json_returns_error(client):
    with client.websocket_connect("/career/ws") as websocket:
        websocket.send_text("{not-json")
        error = websocket.receive_json()

    assert error == {"error": "Invalid JSON"}
