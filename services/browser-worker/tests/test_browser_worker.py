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


# Cita médica de prueba: identificación por CIP + apellido (sin Cl@ve), centro y
# fecha/hora. Son los cinco campos que el worker precompleta en las páginas.
_MED_FIELDS = {
    "health_card_number": "BBBB1234567890",
    "surname": "García",
    "center": "valladolid-pilarica",
    "date": "2026-09-01",
    "time": "09:00",
}


def test_prepare_without_confirmation_prefills_and_hands_off(client):
    """Sin la confirmación del ciudadano, prepara y cede (no reserva)."""
    body = client.post(
        "/worker/prepare",
        json={"connector": "demo.worker.appointment", "fields": _MED_FIELDS},
    ).json()

    assert body["status"] == "user_handoff"
    # Recorrió el asistente hasta la página de confirmación; las selecciones
    # viajan como parámetros del 'Siguiente'.
    assert "/portal/cita/confirmar" in body["url"]
    # Precompletó los cinco campos repartidos en las páginas.
    assert set(body["prefilled"]) == set(_MED_FIELDS)
    # Lo que quedaría en manos de la persona.
    assert "confirmar" in body["pending"]
    kinds = [e["kind"] for e in body["events"]]
    assert kinds[0] == "navigate"
    assert kinds.count("advance") == 3  # identificación -> centro -> fecha -> confirmar
    assert "handoff" in kinds


def test_prepare_with_confirmation_completes_the_appointment(client):
    """Con la confirmación explícita, el worker completa la cita (reversible)."""
    body = client.post(
        "/worker/prepare",
        json={
            "connector": "demo.worker.appointment",
            "fields": _MED_FIELDS,
            "confirm": True,
        },
    ).json()

    assert body["status"] == "completed"
    assert body["reference"].startswith("CITA-")
    assert set(body["prefilled"]) == set(_MED_FIELDS)


def test_worker_never_fills_captcha_even_if_supplied(client):
    """Aunque llegue un valor de CAPTCHA, el worker no lo escribe (regla 5)."""
    body = client.post(
        "/worker/prepare",
        json={
            "connector": "demo.worker.appointment",
            "fields": {**_MED_FIELDS, "captcha": "9999", "clave": "secreto"},
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
            "fields": {
                **_MED_FIELDS,
                "surname": "SENTINEL-NAME",
                "health_card_number": "SENTINEL-CIP",
            },
        },
    ).json()
    assert "SENTINEL-NAME" not in str(body["events"])
    assert "SENTINEL-CIP" not in str(body["events"])


def test_partial_fields_prefill_only_what_is_provided(client):
    """Si faltan datos, precompleta lo que hay y cede igual (no se bloquea)."""
    body = client.post(
        "/worker/prepare",
        json={
            "connector": "demo.worker.appointment",
            "fields": {"health_card_number": "BBBB1234567890", "surname": "García"},
        },
    ).json()
    assert body["status"] == "user_handoff"
    assert set(body["prefilled"]) == {"health_card_number", "surname"}


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


def test_portal_submit_requires_explicit_confirmation(client):
    """Sin la confirmación explícita del ciudadano, el portal rechaza el envío;
    con ella, la cita se completa y devuelve una referencia."""
    assert client.post("/portal/cita/confirmar").status_code == 403
    ok = client.post("/portal/cita/confirmar", data={"confirmado": "si"})
    assert ok.status_code == 200
    assert "CITA-" in ok.text


def test_allowlist_rejects_foreign_host():
    spec = build_registry("worker.local")["demo.worker.appointment"]
    assert spec.allows("http://worker.local/portal/cita") is True
    assert spec.allows("http://evil.example.com/portal/cita") is False


def test_allowlist_rejects_userinfo_and_subdomain_suffix_tricks():
    # Un portal real (https) es el caso realista para estos ataques de URL.
    sacyl = build_registry("worker.local")["sacyl.health.primary-care"]
    assert sacyl.allows("https://cita.saludcastillayleon.es/") is True
    # Truco del userinfo: el host real es malo.com, no el que aparenta.
    assert sacyl.allows("https://cita.saludcastillayleon.es@malo.com/") is False
    # Truco del sufijo: ...es.malo.com es OTRO host, no un subdominio permitido.
    assert sacyl.allows("https://cita.saludcastillayleon.es.malo.com/") is False


def test_allowlist_rejects_scheme_downgrade():
    """No se rellena por HTTP en claro un portal que arranca en HTTPS."""
    sacyl = build_registry("worker.local")["sacyl.health.primary-care"]
    assert sacyl.allows("https://www.saludcastillayleon.es/tramite") is True
    assert sacyl.allows("http://www.saludcastillayleon.es/tramite") is False


def test_allowlist_rejects_non_web_schemes():
    spec = build_registry("worker.local")["demo.worker.appointment"]
    assert spec.allows("javascript:alert(1)") is False
    assert spec.allows("file:///etc/passwd") is False
    assert spec.allows("data:text/html,<script>1</script>") is False
