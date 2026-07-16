from fastapi.testclient import TestClient

from app.main import SPOOL_DIR, app

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


def test_capture_returns_synthetic_image():
    body = client.post("/device/camera/capture").json()
    assert body["status"] == "simulated"
    assert body["mime_type"] == "image/png"
    assert len(body["image_base64"]) > 0
