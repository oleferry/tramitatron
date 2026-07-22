"""Registro de tótems y salud del parque (TT-601, EPIC 6).

Un tótem es un dispositivo: su estado son datos operativos no identificativos
(PRD §9.2). Estos tests fijan la derivación de estado (online/degraded/offline/
unknown), el alta automática, el parque declarado y la protección por token.
"""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.totems.loader import DeclaredTotem, load_totems
from app.totems.models import Peripherals
from app.totems.registry import TotemRegistry


class _Clock:
    """Reloj controlable para tests de ventana temporal."""

    def __init__(self, start: datetime) -> None:
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now = self.now + timedelta(seconds=seconds)


def _declared() -> list[DeclaredTotem]:
    return [
        DeclaredTotem(id="cyl-valladolid-01", label="Valladolid", municipality="Valladolid"),
        DeclaredTotem(id="cyl-burgos-01", label="Burgos", municipality="Burgos"),
    ]


# --- Registro (unidad) -------------------------------------------------------

def test_declared_totem_without_heartbeat_is_offline():
    reg = TotemRegistry(_declared(), now=_Clock(datetime(2026, 7, 22, tzinfo=UTC)))
    view = reg.snapshot()
    assert view.summary.total == 2
    assert view.summary.offline == 2
    for t in view.totems:
        assert t.declared is True
        assert t.state == "offline"
        assert t.last_seen is None
        assert t.version is None


def test_heartbeat_marks_online_then_offline_after_window():
    clock = _Clock(datetime(2026, 7, 22, 10, 0, tzinfo=UTC))
    reg = TotemRegistry(_declared(), now=clock, offline_after_seconds=180)
    reg.heartbeat("cyl-valladolid-01", "0.1.0", Peripherals())

    t = reg.get("cyl-valladolid-01")
    assert t.state == "online"
    assert t.version == "0.1.0"
    assert t.seconds_since_seen == 0.0

    clock.advance(200)  # más de la ventana de 180 s
    assert reg.get("cyl-valladolid-01").state == "offline"


def test_peripheral_down_is_degraded():
    reg = TotemRegistry(_declared(), now=_Clock(datetime(2026, 7, 22, tzinfo=UTC)))
    reg.heartbeat("cyl-valladolid-01", "0.1.0", Peripherals(printer="down"))
    assert reg.get("cyl-valladolid-01").state == "degraded"


def test_low_paper_is_degraded():
    reg = TotemRegistry(_declared(), now=_Clock(datetime(2026, 7, 22, tzinfo=UTC)))
    reg.heartbeat("cyl-burgos-01", "0.1.0", Peripherals(paper_level=5))
    assert reg.get("cyl-burgos-01").state == "degraded"


def test_auto_registration_of_undeclared_totem():
    reg = TotemRegistry(_declared(), now=_Clock(datetime(2026, 7, 22, tzinfo=UTC)))
    reg.heartbeat("pop-up-feria-01", "0.1.0", Peripherals())
    t = reg.get("pop-up-feria-01")
    assert t is not None
    assert t.auto_registered is True
    assert t.declared is False
    assert t.state == "online"
    # Aparece también en el parque, después de los declarados.
    ids = [x.id for x in reg.snapshot().totems]
    assert ids == ["cyl-valladolid-01", "cyl-burgos-01", "pop-up-feria-01"]


def test_empty_fleet_without_yaml(tmp_path):
    assert load_totems(tmp_path / "no-existe.yaml") == []
    reg = TotemRegistry([], now=_Clock(datetime(2026, 7, 22, tzinfo=UTC)))
    assert reg.snapshot().summary.total == 0
    assert reg.get("cualquiera") is None


def test_loader_reads_repo_fleet():
    # El parque real del repo (infra/totems.yaml) carga sin errores.
    fleet = load_totems(Settings().totems_path)
    assert len(fleet) >= 1
    assert all(t.id for t in fleet)


# --- Endpoints ---------------------------------------------------------------

@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app(Settings()))


def test_heartbeat_endpoint_updates_fleet(client: TestClient):
    r = client.post(
        "/api/totems/cyl-valladolid-01/heartbeat",
        json={"version": "0.1.0", "peripherals": {"camera": "ok", "paper_level": 90}},
    )
    assert r.status_code == 204

    fleet = client.get("/api/totems").json()
    by_id = {t["id"]: t for t in fleet["totems"]}
    assert by_id["cyl-valladolid-01"]["state"] == "online"
    assert by_id["cyl-valladolid-01"]["version"] == "0.1.0"


def test_heartbeat_rejects_bad_totem_id(client: TestClient):
    r = client.post("/api/totems/BAD_ID!/heartbeat", json={"version": "0.1.0"})
    assert r.status_code == 422


def test_heartbeat_rejects_extra_fields(client: TestClient):
    r = client.post(
        "/api/totems/cyl-burgos-01/heartbeat",
        json={"version": "0.1.0", "session_id": "nope"},
    )
    assert r.status_code == 422


def test_single_totem_404_when_unknown(client: TestClient):
    assert client.get("/api/totems/no-existe-99").status_code == 404


def test_fleet_carries_no_citizen_data(client: TestClient):
    # Un tótem tiene id/ubicación/versión/periféricos (datos del DISPOSITIVO).
    # Lo que no puede aparecer nunca es dato de la ciudadanía.
    client.post(
        "/api/totems/cyl-leon-01/heartbeat",
        json={"version": "0.1.0", "peripherals": {"scanner": "down"}},
    )
    raw = client.get("/api/totems").text.lower()
    for forbidden in ('"session', '"dni', '"nie', '"audio', '"image', '"text', '"citizen'):
        assert forbidden not in raw


# --- Protección --------------------------------------------------------------

def test_read_requires_admin_token_when_configured():
    client = TestClient(create_app(Settings(admin_token="s3cr3t")))
    assert client.get("/api/totems").status_code == 401
    ok = client.get("/api/totems", headers={"Authorization": "Bearer s3cr3t"})
    assert ok.status_code == 200
    # El latido sigue abierto (dispositivo confiable, sin token de tótem).
    assert client.post("/api/totems/x-01/heartbeat", json={"version": "0.1.0"}).status_code == 204


def test_heartbeat_requires_totem_token_when_configured():
    client = TestClient(create_app(Settings(totem_token="dev1ce")))
    assert client.post("/api/totems/x-01/heartbeat", json={"version": "0.1.0"}).status_code == 401
    ok = client.post(
        "/api/totems/x-01/heartbeat",
        json={"version": "0.1.0"},
        headers={"X-Totem-Token": "dev1ce"},
    )
    assert ok.status_code == 204
