"""Incidencias y soporte (TT-603, EPIC 6).

Fija dos cosas: la redacción del error técnico (nunca se persiste PII, PRD
§13.4) y el ciclo de la incidencia (alta con código anónimo, lista, resolución,
protección del panel). Un trámite que falla abre una incidencia S3 y devuelve
su código al kiosco (PRD §5).
"""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.incidents.redact import redact
from app.incidents.registry import IncidentRegistry
from app.main import create_app

# --- Redacción (PRD §13.4) ---------------------------------------------------

@pytest.mark.parametrize(
    "raw, must_not_contain",
    [
        ("Fallo al enviar el DNI 12345678Z al portal", "12345678Z"),
        ("NIE X1234567L rechazado", "X1234567L"),
        ("Timeout con IBAN ES91 2100 0418 4502 0005 1332", "ES91"),
        ("Error notificando a juan.perez@example.com", "juan.perez@example.com"),
        ("SIP 1234567890 no encontrado", "1234567890"),
        ("Llamada a +34 600 123 456 fallida", "600 123 456"),
    ],
)
def test_redact_removes_personal_data(raw, must_not_contain):
    out = redact(raw)
    assert must_not_contain not in out


def test_redact_keeps_useful_technical_info():
    # Códigos de estado y palabras técnicas se conservan: diagnostican, no identifican.
    out = redact("HTTP 500 timeout tras 3 reintentos en el conector SITVAL")
    assert "500" in out
    assert "timeout" in out
    assert "reintentos" in out


def test_redact_handles_empty_and_caps_length():
    assert redact("") == "(sin detalle)"
    assert redact(None) == "(sin detalle)"
    assert len(redact("x" * 5000)) <= 301


# --- Registro (unidad) -------------------------------------------------------

def test_open_generates_unique_anonymous_code():
    reg = IncidentRegistry()
    a = reg.open(component="connector", technical_error="fallo", connector="demo")
    b = reg.open(component="printer", technical_error="sin papel", severity="S4")
    assert a.code.startswith("INC-")
    assert a.code != b.code
    assert a.status == "open"
    assert a.severity == "S3"
    assert b.severity == "S4"


def test_open_redacts_before_storing():
    reg = IncidentRegistry()
    inc = reg.open(component="connector", technical_error="rechazo del DNI 11111111H")
    assert "11111111H" not in inc.technical_error


def test_resolve_marks_resolved():
    reg = IncidentRegistry()
    inc = reg.open(component="api", technical_error="x")
    resolved = reg.resolve(inc.code, note="reiniciado el conector")
    assert resolved.status == "resolved"
    assert resolved.resolution
    assert reg.resolve("INC-NOEXISTE", "x") is None


def test_summary_counts_open_and_by_severity():
    reg = IncidentRegistry()
    s1 = reg.open(component="api", technical_error="x", severity="S1")
    reg.open(component="connector", technical_error="y", severity="S3")
    reg.resolve(s1.code)
    summary = reg.summary()
    assert summary.total == 2
    assert summary.open == 1  # la S1 quedó resuelta
    assert summary.by_severity["S1"] == 1
    assert summary.by_severity["S3"] == 1


def test_ring_buffer_caps_size():
    reg = IncidentRegistry(max_incidents=3)
    codes = [reg.open(component="api", technical_error=str(i)).code for i in range(5)]
    remaining = {i.code for i in reg.list()}
    assert len(remaining) == 3
    assert codes[0] not in remaining  # la más antigua se descartó
    assert codes[-1] in remaining


# --- Endpoints ---------------------------------------------------------------

@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app(Settings()))


def test_report_returns_code_and_redacts(client: TestClient):
    r = client.post(
        "/api/incidents",
        json={
            "component": "printer",
            "severity": "S4",
            "technical_error": "atasco con SIP 9876543210",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["code"].startswith("INC-")
    assert "9876543210" not in body["technical_error"]


def test_report_rejects_unknown_component(client: TestClient):
    r = client.post("/api/incidents", json={"component": "reactor-nuclear"})
    assert r.status_code == 422


def test_list_filters_by_status_and_severity(client: TestClient):
    client.post("/api/incidents", json={"component": "api", "severity": "S1"})
    client.post("/api/incidents", json={"component": "network", "severity": "S3"})
    all_inc = client.get("/api/incidents").json()
    assert all_inc["summary"]["total"] == 2
    only_s1 = client.get("/api/incidents", params={"severity": "S1"}).json()
    assert len(only_s1["incidents"]) == 1
    assert only_s1["incidents"][0]["severity"] == "S1"


def test_resolve_endpoint(client: TestClient):
    code = client.post("/api/incidents", json={"component": "api"}).json()["code"]
    r = client.post(f"/api/incidents/{code}/resolve", json={"note": "corregido"})
    assert r.status_code == 200
    assert r.json()["status"] == "resolved"
    assert client.get(f"/api/incidents/{code}").json()["status"] == "resolved"


def test_get_unknown_incident_404(client: TestClient):
    assert client.get("/api/incidents/INC-NADA").status_code == 404


# --- Integración: fallo de trámite abre incidencia ---------------------------

def _session(client: TestClient) -> str:
    return client.post("/api/session", json={"language": "es"}).json()["session_id"]


def test_failed_procedure_opens_incident_and_returns_code(client: TestClient):
    # El trámite del worker sin worker configurado devuelve "failed".
    session_id = _session(client)
    r = client.post(
        "/api/procedures/demo.worker.appointment/execute",
        json={"session_id": session_id, "confirmed": True},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "failed"
    assert body["incident_code"] and body["incident_code"].startswith("INC-")
    # Y queda registrada como S3 del componente conector.
    listed = client.get("/api/incidents").json()["incidents"]
    match = [i for i in listed if i["code"] == body["incident_code"]]
    assert match and match[0]["severity"] == "S3"
    assert match[0]["component"] == "connector"
    # La incidencia conserva el DETALLE TÉCNICO del conector (aquí: worker sin
    # configurar), no el mensaje genérico que ve el ciudadano. Es lo que soporte
    # necesita para diagnosticar.
    detail = client.get(f"/api/incidents/{body['incident_code']}").json()
    assert "configurado" in detail["technical_error"]


# --- Privacidad y protección -------------------------------------------------

def test_list_carries_no_personal_data(client: TestClient):
    client.post(
        "/api/incidents",
        json={
            "component": "connector",
            "technical_error": "fallo con DNI 22222222J y correo a@b.com",
        },
    )
    raw = client.get("/api/incidents").text
    assert "22222222J" not in raw
    assert "a@b.com" not in raw


def test_read_and_resolve_require_admin_token_when_configured():
    client = TestClient(create_app(Settings(admin_token="s3cr3t")))
    # La ingesta del kiosco sigue abierta (anónima).
    code = client.post("/api/incidents", json={"component": "api"}).json()["code"]
    assert client.get("/api/incidents").status_code == 401
    assert client.post(f"/api/incidents/{code}/resolve", json={}).status_code == 401
    ok = client.get("/api/incidents", headers={"Authorization": "Bearer s3cr3t"})
    assert ok.status_code == 200
