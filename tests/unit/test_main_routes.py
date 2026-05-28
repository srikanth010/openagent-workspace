def test_root_route(client):
    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "OpenAgent Workspace API"
    assert payload["health"] == "/health"
    assert payload["career_chat"] == "/career/chat"


def test_health_route(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_config_route(client):
    response = client.get("/config")

    assert response.status_code == 200
    payload = response.json()
    assert "ollama_base_url" in payload
    assert "ollama_model" in payload
