import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.core import session_store


@pytest.fixture
def client() -> TestClient:
    session_store.clear()
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions_between_tests():
    session_store.clear()
    yield
    session_store.clear()
