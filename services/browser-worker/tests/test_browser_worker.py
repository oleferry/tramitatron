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


_FULL_FIELDS = {
    "service": "renovacion-dni",
    "office": "valladolid-centro",
    "date": "2026-09-01",
    "time": "09:00",
    "full_name": "Persona de Prueba",
    "dni_number": "12345678Z",
    "phone": "600123456",
}


def test_prepare_walks_wizard_prefills_and_hands_off(client):
    body = client.post(
        "/worker/prepare",
        json={"connector": "demo.worker.appointment", "fields": _FULL_FIELDS},
    ).json()

    # Nunca "completed": el resultado terminal es siempre ceder a la persona.
    assert body["status"] == "user_handoff"
    # Recorrió el asistente hasta el último paso (datos + CAPTCHA); las
    # selecciones viajan como parámetros del 'Siguiente'.
    assert "/portal/cita/datos" in body["url"]
    # Precompletó los siete campos repartidos en las cuatro páginas.
    assert set(body["prefilled"]) == set(_FULL_FIELDS)
    # La persona debe resolver el CAPTCHA y confirmar.
    assert "captcha" in body["pending"]
    assert "confirmar" in body["pending"]
    # Hubo navegación entre pasos (varios 'advance') y un cierre en handoff.
    kinds = [e["kind"] for e in body["events"]]
    assert kinds[0] == "navigate"
    assert kinds.count("advance") == 3  # servicio -> oficina -> fecha -> datos
    assert "handoff" in kinds


def test_worker_never_fills_captcha_even_if_supplied(client):
    """Aunque llegue un valor de CAPTCHA, el worker no lo escribe (regla 5)."""
    body = client.post(
        "/worker/prepare",
        json={
            "connector": "demo.worker.appointment",
            "fields": {**_FULL_FIELDS, "captcha": "9999", "clave": "secreto"},
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
            "fields": {**_FULL_FIELDS, "full_name": "SENTINEL-NAME", "dni_number": "SENTINEL-DNI"},
        },
    ).json()
    assert "SENTINEL-NAME" not in str(body["events"])
    assert "SENTINEL-DNI" not in str(body["events"])


def test_partial_fields_prefill_only_what_is_provided(client):
    """Si faltan datos, precompleta lo que hay y cede igual (no se bloquea)."""
    body = client.post(
        "/worker/prepare",
        json={
            "connector": "demo.worker.appointment",
            "fields": {"service": "renovacion-dni", "office": "burgos-gamonal"},
        },
    ).json()
    assert body["status"] == "user_handoff"
    assert set(body["prefilled"]) == {"service", "office"}


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
    """El portal de pruebas rechaza el POST de confirmación: si el worker
    intentara enviarlo (lo que NO hace), fallaría de forma ruidosa."""
    assert client.post("/portal/cita/confirmar").status_code == 403


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
