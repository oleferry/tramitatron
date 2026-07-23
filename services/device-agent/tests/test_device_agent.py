from fastapi.testclient import TestClient

from app.main import SPOOL_DIR, app, create_app

client = TestClient(app)


def test_health():
    body = client.get("/device/health").json()
    assert body["status"] == "ok"
    assert body["mode"] == "simulator"


def test_print_and_purge():
    response = client.post("/device/printer/print", json={"lines": ["Tramitatrón", "DEMO-1234"]})
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    assert (SPOOL_DIR / f"{job_id}.txt").exists()

    assert client.post("/device/session/purge").json()["status"] == "purged"
    assert not SPOOL_DIR.exists()


def test_print_keeps_only_current_job():
    """Higiene del spool (regla 4): un trabajo nuevo no deja en disco el previo."""
    client.post("/device/session/purge")  # estado limpio
    first = client.post("/device/printer/print", json={"lines": ["uno"]}).json()["job_id"]
    second = client.post("/device/printer/print", json={"lines": ["dos"]}).json()["job_id"]
    assert not (SPOOL_DIR / f"{first}.txt").exists()
    assert (SPOOL_DIR / f"{second}.txt").exists()
    client.post("/device/session/purge")


def test_capture_returns_synthetic_image():
    body = client.post("/device/camera/capture").json()
    assert body["status"] == "simulated"
    assert body["mime_type"] == "image/png"
    assert len(body["image_base64"]) > 0


def test_no_token_means_open_in_dev():
    """Sin token configurado, el agente queda abierto (solo desarrollo)."""
    assert client.get("/device/health").json()["auth"] == "open"


def test_operations_require_token_when_configured():
    """Con token, accionar un periférico exige la cabecera X-Device-Token."""
    secured = TestClient(create_app("token-secreto"))

    # El healthcheck sigue abierto (liveness).
    assert secured.get("/device/health").json()["auth"] == "required"

    # Sin cabecera: 401.
    assert secured.post("/device/camera/capture").status_code == 401
    # Con token incorrecto: 401.
    bad = secured.post("/device/camera/capture", headers={"X-Device-Token": "otro"})
    assert bad.status_code == 401
    # Con el token correcto: 200.
    ok = secured.post("/device/camera/capture", headers={"X-Device-Token": "token-secreto"})
    assert ok.status_code == 200
