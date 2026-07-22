"""Panel institucional y KPIs (TT-602, PRD §18).

El panel solo expone AGREGADOS. Estos tests fijan tanto los números como la
regla de oro: nada de identidad, texto ni datos personales sale por aquí
(PRD §18.2, métricas prohibidas).
"""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.metrics.registry import MetricsRegistry

# --- Registro (unidad) -------------------------------------------------------

def test_registry_counts_sessions_language_and_hour():
    clock = lambda: datetime(2026, 7, 22, 9, 30, tzinfo=UTC)  # noqa: E731
    reg = MetricsRegistry(now=clock)
    reg.record_session("es")
    reg.record_session("es")
    reg.record_session("ca-valencia")

    snap = reg.snapshot()
    assert snap["usage"]["sessions"] == 3
    assert snap["usage"]["by_language"] == {"es": 2, "ca-valencia": 1}
    assert snap["usage"]["by_hour"][9] == 3
    assert snap["usage"]["by_hour"][10] == 0
    # Las 24 franjas están presentes aunque estén a cero.
    assert len(snap["usage"]["by_hour"]) == 24


def test_registry_procedure_rates():
    reg = MetricsRegistry()
    for _ in range(10):
        reg.record_procedure("demo.mock.appointment", "started")
    for _ in range(6):
        reg.record_procedure("demo.mock.appointment", "completed")
    reg.record_procedure("demo.mock.appointment", "handoff")
    reg.record_procedure("demo.mock.appointment", "handoff")

    proc = reg.snapshot()["procedures"]
    assert proc["totals"]["started"] == 10
    assert proc["totals"]["completed"] == 6
    assert proc["totals"]["handoff"] == 2
    assert proc["success_rate_pct"] == 60.0
    assert proc["handoff_rate_pct"] == 20.0
    # Abandono = iniciados no resueltos (10 - 6 - 2) / 10.
    assert proc["abandonment_rate_pct"] == 20.0


def test_registry_rates_are_none_without_data():
    proc = MetricsRegistry().snapshot()["procedures"]
    assert proc["success_rate_pct"] is None
    assert proc["abandonment_rate_pct"] is None


def test_registry_satisfaction_average():
    reg = MetricsRegistry()
    for r in (5, 5, 3):
        reg.record_satisfaction(r)
    sat = reg.snapshot()["satisfaction"]
    assert sat["votes"] == 3
    assert sat["average"] == round((5 + 5 + 3) / 3, 2)
    assert sat["histogram"][5] == 2
    assert sat["histogram"][1] == 0


def test_registry_rejects_bad_input():
    reg = MetricsRegistry()
    with pytest.raises(ValueError):
        reg.record_procedure("x", "hacked")
    with pytest.raises(ValueError):
        reg.record_channel("telepatia")
    with pytest.raises(ValueError):
        reg.record_satisfaction(0)
    with pytest.raises(ValueError):
        reg.record_satisfaction(6)


# --- Endpoints ---------------------------------------------------------------

def _event(client: TestClient, event_type: str, procedure_id: str):
    return client.post(
        "/api/metrics/event", json={"type": event_type, "procedure_id": procedure_id}
    )


def test_event_started_and_abandoned_count(client: TestClient):
    pid = "sacyl.health.primary-care"
    assert _event(client, "started", pid).status_code == 204
    assert _event(client, "abandoned", pid).status_code == 204

    by_proc = client.get("/api/metrics/summary").json()["procedures"]["by_procedure"]
    assert by_proc[pid]["started"] == 1
    assert by_proc[pid]["abandoned"] == 1


def test_event_rejects_unknown_procedure(client: TestClient):
    r = client.post("/api/metrics/event", json={"type": "started", "procedure_id": "no.existe"})
    assert r.status_code == 404


def test_event_rejects_server_only_status(client: TestClient):
    # "completed"/"failed" no se aceptan desde fuera: los registra el servidor.
    r = client.post(
        "/api/metrics/event",
        json={"type": "completed", "procedure_id": "demo.mock.appointment"},
    )
    assert r.status_code == 422


def test_feedback_validates_range(client: TestClient):
    assert client.post("/api/metrics/feedback", json={"rating": 5}).status_code == 204
    assert client.post("/api/metrics/feedback", json={"rating": 0}).status_code == 422
    assert client.post("/api/metrics/feedback", json={"rating": 9}).status_code == 422
    sat = client.get("/api/metrics/summary").json()["satisfaction"]
    assert sat["votes"] == 1
    assert sat["average"] == 5.0


# --- Instrumentación autoritativa del servidor -------------------------------

def _session(client: TestClient) -> str:
    return client.post("/api/session", json={"language": "es"}).json()["session_id"]


def test_creating_session_increments_usage(client: TestClient):
    before = client.get("/api/metrics/summary").json()["usage"]["sessions"]
    _session(client)
    after = client.get("/api/metrics/summary").json()["usage"]["sessions"]
    assert after == before + 1


def test_executing_mock_procedure_counts_completed(client: TestClient):
    session_id = _session(client)
    client.post(
        "/api/procedures/demo.mock.appointment/execute",
        json={"session_id": session_id, "confirmed": True},
    )
    totals = client.get("/api/metrics/summary").json()["procedures"]["by_procedure"]
    assert totals["demo.mock.appointment"]["completed"] == 1


def test_assistant_and_document_channels_count(client: TestClient):
    session_id = _session(client)
    client.post("/api/assistant/ask", json={"text": "cita médico"})
    # Documento: base64 de un byte cualquiera; el mock ignora la imagen.
    client.post(
        f"/api/session/{session_id}/documents",
        json={"document_class": "dni", "image_base64": "AAAA", "mime_type": "image/png"},
    )
    channels = client.get("/api/metrics/summary").json()["usage"]["channels"]
    assert channels["assistant"] >= 1
    assert channels["documents"] >= 1


# --- Privacidad (PRD §18.2) --------------------------------------------------

def test_summary_carries_no_identity_or_free_text(client: TestClient):
    session_id = _session(client)
    client.post("/api/assistant/ask", json={"text": "un texto secreto que no debe aparecer"})

    raw = client.get("/api/metrics/summary").text
    assert session_id not in raw
    assert "secreto" not in raw
    # No hay claves que huelan a identidad o contenido.
    for forbidden in ("session_id", "ip", "user", "text", "audio", "image", "name"):
        assert forbidden not in raw.lower()


def test_csv_export_has_no_personal_data(client: TestClient):
    session_id = _session(client)
    r = client.get("/api/metrics/summary.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "attachment" in r.headers["content-disposition"]
    assert session_id not in r.text
    assert r.text.startswith("seccion,clave,valor")


# --- Protección del panel (threat model D3) ----------------------------------

def _admin_client(token: str) -> TestClient:
    return TestClient(create_app(Settings(admin_token=token)))


def test_summary_requires_token_when_configured():
    client = _admin_client("s3cr3t")
    assert client.get("/api/metrics/summary").status_code == 401
    ok = client.get("/api/metrics/summary", headers={"Authorization": "Bearer s3cr3t"})
    assert ok.status_code == 200
    # La ingesta del kiosco sigue abierta: es anónima.
    assert client.post("/api/metrics/feedback", json={"rating": 4}).status_code == 204
