"""Conector de navegación asistida (API -> worker).

Fija el mapeo del resultado del worker al contrato de conector y, sobre todo,
que un tótem SIN worker no se rompe: informa de que no está disponible.
"""

import asyncio

import httpx

from app.connectors.worker import WorkerConnector


def _connector(handler, *, worker_connector="demo.worker.appointment") -> WorkerConnector:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://worker")
    return WorkerConnector(
        name="connectors.worker.demo",
        worker_url="http://worker",
        worker_connector=worker_connector,
        client=client,
    )


def test_handoff_is_mapped_to_execution_result():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/worker/prepare"
        return httpx.Response(
            200,
            json={
                "status": "user_handoff",
                "connector": "demo.worker.appointment",
                "url": "http://portal/cita",
                "prefilled": ["license_plate"],
                "pending": ["captcha", "confirmar"],
                "events": [],
            },
        )

    connector = _connector(handler)
    result = asyncio.run(connector.execute({"license_plate": "1234ABC"}, confirmed=True))
    assert result.status == "user_handoff"
    assert result.receipt["url"] == "http://portal/cita"
    assert result.receipt["pending"] == "captcha, confirmar"


def test_unavailable_worker_result_becomes_failed():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"status": "unavailable", "connector": "x", "message": "gated"}
        )

    result = asyncio.run(_connector(handler).execute({}, confirmed=True))
    assert result.status == "failed"
    assert result.message == "gated"


def test_execute_requires_confirmation():
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - no debe llamarse
        raise AssertionError("no debe llamarse al worker sin confirmación")

    result = asyncio.run(_connector(handler).execute({}, confirmed=False))
    assert result.status == "failed"


def test_worker_error_is_reported_not_raised():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    result = asyncio.run(_connector(handler).execute({}, confirmed=True))
    assert result.status == "failed"
    assert "no está disponible" in result.message


def test_unconfigured_worker_fails_cleanly():
    connector = WorkerConnector(
        name="connectors.worker.demo", worker_url=None, worker_connector="demo.worker.appointment"
    )
    result = asyncio.run(connector.execute({}, confirmed=True))
    assert result.status == "failed"
    healthcheck = asyncio.run(connector.healthcheck())
    assert healthcheck.healthy is False


def test_healthcheck_maps_worker_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/worker/healthcheck/" in request.url.path
        return httpx.Response(200, json={"connector": "x", "healthy": True, "detail": "ok"})

    result = asyncio.run(_connector(handler).healthcheck())
    assert result.healthy is True


def test_api_reports_worker_procedure_unavailable_without_worker(client):
    """Vía API, sin worker configurado, el trámite falla con mensaje, no 500."""
    session_id = client.post("/api/session", json={"language": "es"}).json()["session_id"]
    response = client.post(
        "/api/procedures/demo.worker.appointment/execute",
        json={"session_id": session_id, "confirmed": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["message"]
