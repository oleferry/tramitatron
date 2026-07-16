import pytest

from app.catalog.loader import CatalogError, load_catalog


def test_catalog_lists_procedures(client):
    body = client.get("/api/catalog").json()
    ids = {item["id"] for item in body}
    assert "demo.mock.appointment" in ids
    assert "gva.health.primary-care.appointment" in ids
    assert "sitval.itv.appointment" in ids


def test_procedure_detail_is_bilingual(client):
    body = client.get("/api/catalog/gva.health.primary-care.appointment").json()
    assert body["name"]["es"] == "Cita de atención primaria"
    assert body["name"]["ca-valencia"] == "Cita d'atenció primària"
    assert body["status"] == "coming_soon"
    assert body["captcha_policy"] == "user_only"
    assert body["document_retention"] == "none"


def test_unknown_procedure_404(client):
    assert client.get("/api/catalog/no.existe").status_code == 404


def test_invalid_yaml_fails_loudly(tmp_path):
    (tmp_path / "malo.yaml").write_text(
        "id: malo\nname:\n  es: Solo castellano\n", encoding="utf-8"
    )
    with pytest.raises(CatalogError):
        load_catalog(tmp_path)


def test_empty_catalog_fails(tmp_path):
    with pytest.raises(CatalogError):
        load_catalog(tmp_path)
