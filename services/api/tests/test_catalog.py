import pytest

from app.catalog.loader import CatalogError, load_catalog


def test_catalog_lists_procedures(client):
    body = client.get("/api/catalog").json()
    ids = {item["id"] for item in body}
    assert "demo.mock.appointment" in ids
    assert "sacyl.health.primary-care" in ids
    assert "jcyl.itv.info" in ids


def test_procedure_detail_is_bilingual(client):
    body = client.get("/api/catalog/sacyl.health.primary-care").json()
    assert body["name"]["es"] == "Cita de atención primaria"
    assert body["name"]["ca-valencia"] == "Cita d'atenció primària"
    assert body["status"] == "coming_soon"
    assert body["captcha_policy"] == "user_only"
    assert body["document_retention"] == "none"


def test_catalog_includes_expanded_procedures(client):
    """El catálogo ampliado (DNI, Hacienda, Seguridad Social, SEPE, DGT…) carga entero."""
    body = client.get("/api/catalog").json()
    ids = {item["id"] for item in body}
    expected = {
        "mir.dni.renewal-appointment",
        "aeat.cita-previa",
        "seg-social.inss.cita-previa",
        "seg-social.tgss.vida-laboral",
        "sacyl.health.card",
        "sepe.cita-previa",
        "dgt.cita-previa",
        "mir.extranjeria.cita-previa",
        "padron.certificado",
        "mjusticia.certificado-nacimiento",
        "mjusticia.antecedentes-penales",
    }
    assert expected <= ids


def test_information_procedures_are_available_without_connector(client):
    """Los trámites informativos están disponibles pero no capturan datos (A0)."""
    body = client.get("/api/catalog/mjusticia.antecedentes-penales").json()
    assert body["status"] == "available"
    assert body["execution_mode"] == "information"
    assert body["required_fields"] == []
    assert body["risk_class"] == "A0"


def test_automated_connectors_stay_coming_soon(client):
    """PRD §5: DNI, Seguridad Social y AEAT no deben ser conectores automáticos aún."""
    for pid in ("mir.dni.renewal-appointment", "aeat.cita-previa", "seg-social.inss.cita-previa"):
        body = client.get(f"/api/catalog/{pid}").json()
        assert body["status"] == "coming_soon", pid
        assert body["captcha_policy"] == "user_only", pid


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
