def _session(client) -> str:
    return client.post("/api/session", json={"language": "es"}).json()["session_id"]


def test_connectors_health(client):
    body = client.get("/api/connectors/health").json()
    by_id = {c["connector"]: c for c in body}
    assert by_id["demo.mock"] == {"connector": "demo.mock", "healthy": True, "detail": "simulado"}
    # El conector del worker existe; sin worker configurado, no está sano.
    assert by_id["connectors.worker.demo"]["healthy"] is False
    assert by_id["connectors.worker.demo"]["detail"] == "no configurado"


def test_execute_requires_confirmation(client):
    session_id = _session(client)
    response = client.post(
        "/api/procedures/demo.mock.appointment/execute",
        json={"session_id": session_id, "confirmed": False},
    )
    assert response.status_code == 400


def test_execute_mock_procedure(client):
    session_id = _session(client)
    response = client.post(
        "/api/procedures/demo.mock.appointment/execute",
        json={"session_id": session_id, "confirmed": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["receipt"]["reference"].startswith("DEMO-")


def test_coming_soon_procedure_cannot_execute(client):
    session_id = _session(client)
    response = client.post(
        "/api/procedures/sitval.itv.appointment/execute",
        json={"session_id": session_id, "confirmed": True},
    )
    assert response.status_code == 409


def test_execute_without_session_404(client):
    response = client.post(
        "/api/procedures/demo.mock.appointment/execute",
        json={"session_id": "no-existe", "confirmed": True},
    )
    assert response.status_code == 404
