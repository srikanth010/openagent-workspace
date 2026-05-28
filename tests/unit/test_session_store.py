from apps.api.app.core import session_store


def test_get_history_for_missing_session_returns_empty_list():
    assert session_store.get_history("missing") == []


def test_append_turn_and_limit_history():
    session_id = "s1"
    for i in range(12):
        session_store.append_turn(session_id, "user", f"msg-{i}")

    history = session_store.get_history(session_id, limit=10)
    assert len(history) == 10
    assert history[0]["content"] == "msg-2"
    assert history[-1]["content"] == "msg-11"


def test_evict_stale_removes_expired_sessions_only():
    active = session_store.get_or_create_session("active")
    stale = session_store.get_or_create_session("stale")

    stale.last_active = 0
    active.last_active = 10**10

    removed = session_store.evict_stale(ttl_seconds=1)

    assert removed == 1
    assert session_store.get_history("stale") == []
    assert "active" in session_store._sessions


def test_get_or_create_session_updates_last_active_for_existing_session(monkeypatch):
    s = session_store.get_or_create_session("same")
    original_last_active = s.last_active

    monkeypatch.setattr(session_store.time, "time", lambda: original_last_active + 100)
    same = session_store.get_or_create_session("same")

    assert same is s
    assert same.last_active == original_last_active + 100
