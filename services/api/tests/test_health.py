def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "tramitatron-api"


def test_version_reports_deployed_version_and_inventory(client):
    """Versión desplegada e inventario cargado (TT-604)."""
    body = client.get("/api/version").json()
    assert body["service"] == "tramitatron-api"
    assert body["version"]  # p. ej. "0.1.0"
    # El health y /api/version coinciden en la versión.
    assert body["version"] == client.get("/health").json()["version"]
    # El inventario refleja lo cargado al arrancar.
    assert body["catalog_procedures"] >= 1
    assert body["knowledge_sources"] >= 1
