"""Límite de peticiones (ENS mp.s.2, threat model D4)."""

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.ratelimit import RateLimiter


def test_rate_limiter_unit_counts_and_resets():
    limiter = RateLimiter(max_requests=2, window_seconds=10)
    assert limiter.check("a", now=0)[0] is True
    assert limiter.check("a", now=1)[0] is True
    allowed, retry = limiter.check("a", now=2)
    assert allowed is False and retry > 0
    # Otra clave no se ve afectada.
    assert limiter.check("b", now=2)[0] is True
    # Al pasar la ventana, se reinicia.
    assert limiter.check("a", now=11)[0] is True


def test_disabled_when_zero():
    limiter = RateLimiter(max_requests=0, window_seconds=60)
    assert limiter.enabled is False
    assert all(limiter.check("a", now=i)[0] for i in range(100))


def test_flood_gets_429_with_retry_after():
    client = TestClient(create_app(Settings(rate_limit_requests=3, rate_limit_window_seconds=60)))
    codes = [client.get("/api/catalog").status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200]
    assert codes[3] == 429
    response = client.get("/api/catalog")
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) >= 1


def test_health_is_never_rate_limited():
    client = TestClient(create_app(Settings(rate_limit_requests=2, rate_limit_window_seconds=60)))
    for _ in range(10):
        assert client.get("/health").status_code == 200


def test_default_limit_does_not_break_normal_use():
    client = TestClient(create_app(Settings()))
    for _ in range(30):
        assert client.get("/api/catalog").status_code == 200
