"""Worker de navegación asistida (TT-502 y TT-505).

Lo que se fija: el worker prepara (navega y precompleta lo seguro) pero SIEMPRE
cede a la persona (nunca "completed", nunca envía), respeta la allowlist, no
toca campos de CAPTCHA/credenciales, y los portales reales están desactivados.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.registry import build_registry


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app(Settings()))


def test_health(client):
    body = client.get("/worker/health").json()
    assert body["status"] == "ok"
    assert body["driver"] == "simulated"


def test_prepare_navigates_prefills_and_hands_off(client):
    body = client.post(
        "/worker/prepare",
        json={
            "connector": "demo.worker.appointment",
            "fields": {"license_plate": "1234ABC", "vehicle_type": "coche"},
        },
    ).json()

    # Nunca "completed": el resultado terminal es siempre ceder a la persona.
    assert body["status"] == "user_handoff"
    assert body["url"].endswith("/portal/cita")
    assert set(body["prefilled"]) == {"license_plate", "vehicle_type"}
    # La persona debe resolver el CAPTCHA y confirmar.
    assert "captcha" in body["pending"]
    assert "confirmar" in body["pending"]
    kinds = [e["kind"] for e in body["events"]]
    assert kinds[0] == "navigate"
    assert "handoff" in kinds


def test_worker_never_fills_captcha_even_if_supplied(client):
    """Aunque llegue un valor de CAPTCHA, el worker no lo escribe (regla 5)."""
    body = client.post(
        "/worker/prepare",
        json={
            "connector": "demo.worker.appointment",
            "fields": {"license_plate": "1234ABC", "captcha": "9999", "clave": "secreto"},
        },
    ).json()
    assert "captcha" not in body["prefilled"]
    assert "clave" not in body["prefilled"]
    fill_details = [e["detail"] for e in body["events"] if e["kind"] == "fill"]
    assert "captcha" not in fill_details
    assert "clave" not in fill_details


def test_events_never_contain_field_values(client):
    """Los eventos registran el nombre del campo, nunca el valor (PII)."""
    body = client.post(
        "/worker/prepare",
        json={
            "connector": "demo.worker.appointment",
            "fields": {"license_plate": "SENTINEL-PLATE", "vehicle_type": "coche"},
        },
    ).json()
    assert "SENTINEL-PLATE" not in str(body["events"])


def test_real_portals_are_disabled(client):
    """Dirigir la automatización a un portal real está gated (privacidad/EIPD)."""
    body = client.post(
        "/worker/prepare",
        json={"connector": "sacyl.health.primary-care", "fields": {"health_card_number": "123"}},
    ).json()
    assert body["status"] == "unavailable"
    assert body["url"] is None


def test_unknown_connector_404(client):
    response = client.post("/worker/prepare", json={"connector": "no.existe", "fields": {}})
    assert response.status_code == 404


def test_healthcheck_synthetic_ok(client):
    body = client.post("/worker/healthcheck/demo.worker.appointment").json()
    assert body["healthy"] is True
    assert "formulario" in (body["detail"] or "")


def test_healthcheck_disabled_connector(client):
    body = client.post("/worker/healthcheck/sacyl.health.primary-care").json()
    assert body["healthy"] is False
    assert body["detail"] == "desactivado"


def test_portal_submit_is_forbidden(client):
    """El portal de pruebas rechaza el POST: si el worker intentara enviar el
    formulario (lo que NO hace), fallaría de forma ruidosa."""
    assert client.post("/portal/cita").status_code == 403


def test_allowlist_rejects_foreign_host():
    spec = build_registry("worker.local")["demo.worker.appointment"]
    assert spec.allows("http://worker.local/portal/cita") is True
    assert spec.allows("http://evil.example.com/portal/cita") is False
