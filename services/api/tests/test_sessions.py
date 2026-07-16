"""Ciclo de vida de la sesión efímera: creación, datos, purga, expiración
y aislamiento entre usuarios (caso E2E-05 del PRD)."""

import time


def _create(client, language="es") -> str:
    response = client.post("/api/session", json={"language": language})
    assert response.status_code == 201
    return response.json()["session_id"]


def test_create_and_get_session(client):
    session_id = _create(client)
    response = client.get(f"/api/session/{session_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "es"
    assert body["data_keys"] == []
    assert body["expires_in_seconds"] > 0


def test_invalid_language_rejected(client):
    response = client.post("/api/session", json={"language": "en"})
    assert response.status_code == 422


def test_data_keys_visible_but_values_never_returned(client):
    session_id = _create(client)
    response = client.put(
        f"/api/session/{session_id}/data",
        json={"key": "sip_number", "value": "SIP-SECRETO-123456"},
    )
    assert response.status_code == 204

    body = client.get(f"/api/session/{session_id}").json()
    assert body["data_keys"] == ["sip_number"]
    assert "SIP-SECRETO-123456" not in body.__repr__()


def test_purge_is_idempotent_and_session_gone(client):
    session_id = _create(client)
    assert client.delete(f"/api/session/{session_id}").status_code == 204
    assert client.get(f"/api/session/{session_id}").status_code == 404
    # Segunda purga: también 204 (idempotente)
    assert client.delete(f"/api/session/{session_id}").status_code == 204


def test_isolation_between_users(client):
    """Usuario A introduce datos y termina; el usuario B no puede ver nada."""
    session_a = _create(client)
    client.put(
        f"/api/session/{session_a}/data",
        json={"key": "dni_number", "value": "12345678Z"},
    )
    client.delete(f"/api/session/{session_a}")

    session_b = _create(client, language="ca-valencia")
    assert session_b != session_a
    body = client.get(f"/api/session/{session_b}").json()
    assert body["data_keys"] == []
    # La sesión de A ya no existe para nadie
    assert client.get(f"/api/session/{session_a}").status_code == 404


def test_session_expires_and_is_purged(short_ttl_client):
    session_id = _create(short_ttl_client)
    short_ttl_client.put(
        f"/api/session/{session_id}/data",
        json={"key": "phone", "value": "600000000"},
    )
    time.sleep(0.3)
    assert short_ttl_client.get(f"/api/session/{session_id}").status_code == 404


def test_extend_renews_ttl(short_ttl_client):
    session_id = _create(short_ttl_client)
    time.sleep(0.1)
    assert short_ttl_client.post(f"/api/session/{session_id}/extend").status_code == 200
    time.sleep(0.15)
    # Sin extend habría expirado (TTL 0.2s); con extend sigue viva.
    assert short_ttl_client.get(f"/api/session/{session_id}").status_code == 200
