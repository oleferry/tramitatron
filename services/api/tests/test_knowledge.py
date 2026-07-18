"""RAG de contenido oficial (TT-303): la respuesta es un extracto literal de
la fuente, con organismo y fecha; sin fuente relevante no hay respuesta."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.knowledge.ingest import _TextExtractor
from app.main import create_app

FIXTURES = Path(__file__).parent / "fixtures" / "knowledge"


@pytest.fixture()
def kclient() -> TestClient:
    return TestClient(create_app(Settings(knowledge_path=FIXTURES)))


def _ask(client, text, procedure_id=None):
    body = {"text": text}
    if procedure_id:
        body["procedure_id"] = procedure_id
    response = client.post("/api/assistant/ask", json=body)
    assert response.status_code == 200
    return response.json()


def test_ask_returns_official_excerpt_with_source(kclient):
    result = _ask(kclient, "¿Qué necesito para pedir cita con el médico?")
    assert result["found"] is True
    assert "tarjeta SIP" in result["answer"]
    assert result["source"]["organismo"] == "Conselleria de Prueba"
    assert result["source"]["fetched_at"] == "2026-07-15"
    assert result["source"]["url"].startswith("https://ejemplo-oficial.gva.es")


def test_ask_itv_finds_itv_source(kclient):
    result = _ask(kclient, "¿Qué documentos hacen falta para la ITV del vehículo?")
    assert result["found"] is True
    assert result["source"]["organismo"] == "SITVAL de Prueba"
    assert "matrícula" in result["answer"]


def test_ask_prefers_procedure_sources(kclient):
    # "cita" aparece en ambas fuentes; el contexto del trámite desempata.
    result = _ask(kclient, "cita previa internet", procedure_id="sitval.itv.appointment")
    assert result["source"]["organismo"] == "SITVAL de Prueba"


def test_procedure_sources_have_strict_priority(kclient):
    """Dentro de un trámite, responde SU fuente aunque otra puntúe más alto;
    solo si sus fuentes no dicen nada se busca en el resto (fallback)."""
    # "cita previa internet" aparece en AMBAS fuentes; el trámite decide.
    result = _ask(
        kclient, "cita previa internet",
        procedure_id="gva.health.primary-care.appointment",
    )
    assert result["found"] is True
    assert result["source"]["organismo"] == "Conselleria de Prueba"
    # Fallback: el trámite de salud no habla de matrículas; se busca fuera.
    result = _ask(
        kclient, "matrícula del vehículo",
        procedure_id="gva.health.primary-care.appointment",
    )
    assert result["found"] is True
    assert result["source"]["organismo"] == "SITVAL de Prueba"


def test_ask_unknown_topic_returns_not_found(kclient):
    result = _ask(kclient, "quiero adoptar un dinosaurio en marte")
    assert result["found"] is False
    assert result["answer"] is None
    assert result["source"] is None


def test_sources_status_includes_pending(kclient):
    body = kclient.get("/api/knowledge/sources").json()
    by_id = {s["id"]: s for s in body}
    assert by_id["test-salud"]["snapshot_status"] == "ok"
    assert by_id["test-sin-snapshot"]["snapshot_status"] == "pending"
    assert by_id["test-sin-snapshot"]["fetched_at"] is None


def test_empty_knowledge_degrades_safely(tmp_path):
    client = TestClient(create_app(Settings(knowledge_path=tmp_path)))
    result = _ask(client, "cita médico")
    assert result["found"] is False
    assert client.get("/api/knowledge/sources").json() == []


def test_html_extractor_skips_scripts_and_reads_meta():
    extractor = _TextExtractor()
    extractor.feed(
        "<html><head><title>t</title>"
        '<meta name="description" content="Descripción oficial del servicio.">'
        "<script>var secreto = 1;</script></head>"
        "<body><p>Párrafo visible.</p><style>.x{}</style></body></html>"
    )
    text = extractor.text()
    assert "Descripción oficial del servicio." in text
    assert "Párrafo visible." in text
    assert "secreto" not in text
    assert ".x{}" not in text


def test_real_knowledge_dir_loads_in_default_app(client):
    """La app por defecto carga el knowledge/ real del repo sin errores."""
    body = client.get("/api/knowledge/sources").json()
    assert len(body) >= 4
