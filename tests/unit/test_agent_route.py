from apps.api.app.routes import agent as agent_route


def test_agent_chat_generates_session_and_returns_response(client, monkeypatch):
    monkeypatch.setattr(agent_route, "run_chat_agent", lambda message, history=None: "mocked-reply")

    response = client.post("/agent/chat", json={"message": "hello"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["input"] == "hello"
    assert payload["response"] == "mocked-reply"
    assert payload["session_id"]


def test_agent_chat_reuses_trimmed_session_id(client, monkeypatch):
    monkeypatch.setattr(agent_route, "run_chat_agent", lambda message, history=None: "ok")

    response = client.post("/agent/chat", json={"message": "hello", "session_id": "  abc-123  "})

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "abc-123"
