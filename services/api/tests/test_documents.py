"""Flujo documental efímero completo (caso E2E-02 del PRD, con datos sintéticos):
captura → extracción → revisión → confirmación → uso en sesión → purga."""

import base64

TINY_PNG_B64 = base64.b64encode(b"png-sintetico-de-prueba").decode()


def _session(client) -> str:
    return client.post("/api/session", json={"language": "es"}).json()["session_id"]


def _upload(client, session_id, document_class="dni"):
    return client.post(
        f"/api/session/{session_id}/documents",
        json={"document_class": document_class, "image_base64": TINY_PNG_B64},
    )


def test_upload_extracts_and_flags_low_confidence(client):
    session_id = _session(client)
    response = _upload(client, session_id)
    assert response.status_code == 201
    body = response.json()
    fields = {f["field"]: f for f in body["fields"]}

    assert fields["dni_number"]["status"] == "VALID"
    assert fields["dni_number"]["validator"] == "dni_or_nie_v1"
    # birth_date llega con confianza 0.62 -> revisión obligatoria
    assert fields["birth_date"]["status"] == "REVIEW_REQUIRED"

    # La extracción vive dentro de la sesión (solo la clave es visible)
    keys = client.get(f"/api/session/{session_id}").json()["data_keys"]
    assert f"document_{body['document_id']}" in keys


def test_confirm_writes_fields_and_removes_extraction(client):
    session_id = _session(client)
    doc = _upload(client, session_id).json()

    response = client.post(
        f"/api/session/{session_id}/documents/{doc['document_id']}/confirm",
        json={
            "fields": {
                "dni_number": "12345678Z",
                "full_name": "PERSONA SINTÉTICA DEMO",
                "birth_date": "1957-03-14",
            }
        },
    )
    assert response.status_code == 200
    assert response.json()["accepted"] is True

    keys = client.get(f"/api/session/{session_id}").json()["data_keys"]
    assert "dni_number" in keys
    assert "birth_date" in keys
    # La extracción cruda se ha eliminado tras confirmar
    assert not any(k.startswith("document_") for k in keys)


def test_confirm_rejects_invalid_dni(client):
    session_id = _session(client)
    doc = _upload(client, session_id).json()

    response = client.post(
        f"/api/session/{session_id}/documents/{doc['document_id']}/confirm",
        json={"fields": {"dni_number": "12345678A"}},  # letra incorrecta
    )
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is False
    assert body["fields"][0]["status"] == "INVALID"

    # Nada se ha escrito en la sesión y el documento sigue pendiente
    keys = client.get(f"/api/session/{session_id}").json()["data_keys"]
    assert "dni_number" not in keys
    assert f"document_{doc['document_id']}" in keys


def test_confirm_rejects_unknown_fields(client):
    session_id = _session(client)
    doc = _upload(client, session_id).json()
    response = client.post(
        f"/api/session/{session_id}/documents/{doc['document_id']}/confirm",
        json={"fields": {"phone": "600000000"}},
    )
    assert response.status_code == 422


def test_document_purged_with_session(client):
    session_id = _session(client)
    doc = _upload(client, session_id).json()
    client.delete(f"/api/session/{session_id}")

    # Nueva sesión: no hereda absolutamente nada
    other = _session(client)
    keys = client.get(f"/api/session/{other}").json()["data_keys"]
    assert keys == []
    # Y el documento de la sesión purgada ya no existe para nadie
    response = client.post(
        f"/api/session/{session_id}/documents/{doc['document_id']}/confirm",
        json={"fields": {"dni_number": "12345678Z"}},
    )
    assert response.status_code == 404


def test_explicit_document_purge(client):
    session_id = _session(client)
    doc = _upload(client, session_id).json()
    assert (
        client.delete(
            f"/api/session/{session_id}/documents/{doc['document_id']}"
        ).status_code
        == 204
    )
    keys = client.get(f"/api/session/{session_id}").json()["data_keys"]
    assert not any(k.startswith("document_") for k in keys)


def test_invalid_base64_rejected(client):
    session_id = _session(client)
    response = client.post(
        f"/api/session/{session_id}/documents",
        json={"document_class": "dni", "image_base64": "esto-no-es-base64!!!"},
    )
    assert response.status_code == 400


def test_sip_card_extraction(client):
    session_id = _session(client)
    body = _upload(client, session_id, document_class="sip_card").json()
    fields = {f["field"]: f for f in body["fields"]}
    assert fields["sip_number"]["validator"] == "sip_format_v1"
    assert fields["sip_number"]["status"] == "VALID"
