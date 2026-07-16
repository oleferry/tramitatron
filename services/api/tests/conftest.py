import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    app = create_app(Settings())
    return TestClient(app)


@pytest.fixture()
def short_ttl_client() -> TestClient:
    """Cliente con TTL de sesión muy corto para probar la expiración."""
    app = create_app(Settings(session_ttl_seconds=0.2))
    return TestClient(app)
