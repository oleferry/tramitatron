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


def test_session_data_values_never_in_any_response_listing(client):
    session_id = client.post("/api/session", json={"language": "es"}).json()["session_id"]
    client.put(
        f"/api/session/{session_id}/data",
        json={"key": "sip_number", "value": SENTINEL_DNI},
    )
    response = client.get(f"/api/session/{session_id}")
    assert SENTINEL_DNI not in response.text
