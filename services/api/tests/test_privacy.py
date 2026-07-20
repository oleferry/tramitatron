"""Suite de privacidad (TT-203, versión inicial): ningún dato personal que
entre en el sistema puede aparecer en los logs de la aplicación."""

import logging

SENTINEL_DNI = "99887766X-CENTINELA"
SENTINEL_TEXT = "me llamo Centinela Apellido y mi teléfono es 699112233"


def test_no_pii_in_logs(client, caplog):
    with caplog.at_level(logging.DEBUG):
        session_id = client.post("/api/session", json={"language": "es"}).json()["session_id"]
        client.put(
            f"/api/session/{session_id}/data",
            json={"key": "dni_number", "value": SENTINEL_DNI},
        )
        client.post("/api/assistant/intent", json={"text": SENTINEL_TEXT})
        client.delete(f"/api/session/{session_id}")

    all_logs = "\n".join(record.getMessage() for record in caplog.records)
    assert SENTINEL_DNI not in all_logs
    assert "699112233" not in all_logs
    assert "Centinela" not in all_logs


def test_access_log_has_no_query_strings(client, caplog):
    with caplog.at_level(logging.INFO, logger="tramitatron.access"):
        client.get("/api/catalog?secreto=SENTINEL-QUERY")

    all_logs = "\n".join(record.getMessage() for record in caplog.records)
    assert "SENTINEL-QUERY" not in all_logs
    assert "GET /api/catalog" in all_logs


def test_no_document_data_in_logs(client, caplog):
    """Los valores extraídos de un documento (aunque sean sintéticos) jamás
    aparecen en los logs, solo viajan en la respuesta al kiosco."""
    import base64
    import logging

    with caplog.at_level(logging.DEBUG):
        session_id = client.post("/api/session", json={"language": "es"}).json()["session_id"]
        client.post(
            f"/api/session/{session_id}/documents",
            json={
                "document_class": "dni",
                "image_base64": base64.b64encode(b"foto-sintetica").decode(),
            },
        )
        client.delete(f"/api/session/{session_id}")

    all_logs = "\n".join(record.getMessage() for record in caplog.records)
    assert "12345678Z" not in all_logs
    assert "SINTÉTICA" not in all_logs
    assert "1957-03-14" not in all_logs


def test_no_letter_content_in_logs(client, caplog):
    """El texto de una carta administrativa es lo más sensible que maneja el
    sistema (deudas, embargos, importes): jamás puede llegar a los logs."""
    import base64

    with caplog.at_level(logging.DEBUG):
        session_id = client.post("/api/session", json={"language": "es"}).json()["session_id"]
        client.post(
            f"/api/session/{session_id}/letters",
            json={"image_base64": base64.b64encode(b"x" * 64).decode()},
        )
        client.delete(f"/api/session/{session_id}")

    all_logs = "\n".join(record.getMessage() for record in caplog.records)
    for secret in ("PROVIDENCIA", "embargo", "1.240,50", "12345678Z", "2026/EJ/004521"):
        assert secret not in all_logs, secret


def test_letter_excerpt_not_exposed_in_session_listing(client):
    """El listado de la sesión muestra las claves, nunca el texto de la carta."""
    import base64

    session_id = client.post("/api/session", json={"language": "es"}).json()["session_id"]
    client.post(
        f"/api/session/{session_id}/letters",
        json={"image_base64": base64.b64encode(b"x" * 64).decode()},
    )
    response = client.get(f"/api/session/{session_id}")
    assert "PROVIDENCIA" not in response.text
    assert "12345678Z" not in response.text


def test_session_data_values_never_in_any_response_listing(client):
    session_id = client.post("/api/session", json={"language": "es"}).json()["session_id"]
    client.put(
        f"/api/session/{session_id}/data",
        json={"key": "sip_number", "value": SENTINEL_DNI},
    )
    response = client.get(f"/api/session/{session_id}")
    assert SENTINEL_DNI not in response.text
