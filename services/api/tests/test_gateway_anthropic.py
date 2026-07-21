"""Gateway de IA real (PRD §10) con un cliente Claude falso — sin red.

Lo que se fija aquí es el contrato y, sobre todo, las posturas de privacidad:
los documentos y las cartas (datos A2) NO salen a un proveedor externo mientras
`allow_documents` esté apagado, la voz nunca usa el proveedor, y cualquier fallo
degrada sin inventar datos.
"""

import asyncio
import base64
import json

import pytest

from app.catalog.loader import load_catalog
from app.config import Settings
from app.gateway.anthropic_gateway import AnthropicModelGateway
from app.gateway.base import AudioRequest, DocumentRequest, ExplainRequest, IntentRequest
from app.gateway.mock import MockModelGateway
from app.main import _build_gateway

IMG = base64.b64encode(b"x" * 64).decode()


# --- Cliente Claude falso --------------------------------------------------


class _Block:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _Resp:
    def __init__(self, text: str, stop_reason: str | None = None) -> None:
        self.content = [_Block(text)]
        self.stop_reason = stop_reason


class _Messages:
    def __init__(self, fn) -> None:
        self._fn = fn
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return self._fn(kwargs)


class FakeClient:
    """`fn(kwargs)` devuelve un `_Resp` o lanza para simular un fallo."""

    def __init__(self, fn) -> None:
        self.messages = _Messages(fn)


@pytest.fixture()
def catalog():
    return load_catalog(Settings().catalog_path)


def _gw(catalog, fn, *, allow_documents=False):
    return AnthropicModelGateway(
        api_key=None,
        model="claude-opus-4-8",
        catalog=catalog,
        fallback=MockModelGateway(),
        allow_documents=allow_documents,
        client=FakeClient(fn),
    )


def _json_resp(payload: dict, stop_reason: str | None = None) -> _Resp:
    return _Resp(json.dumps(payload), stop_reason=stop_reason)


# --- Selección de gateway --------------------------------------------------


def test_default_gateway_is_mock(catalog):
    """Sin clave, el gateway es el mock: nada sale de la máquina (regla 12)."""
    assert isinstance(_build_gateway(Settings(), catalog), MockModelGateway)


# --- Intención (texto) -----------------------------------------------------


def test_intent_returns_matched_procedure(catalog):
    gw = _gw(
        catalog,
        lambda kw: _json_resp(
            {
                "procedure_id": "mir.dni.renewal-appointment",
                "confidence": 0.9,
                "clarification": None,
            }
        ),
    )
    result = asyncio.run(gw.classify_intent(IntentRequest(text="renovar el dni")))
    assert result.procedure_id == "mir.dni.renewal-appointment"
    assert result.next_action == "SHOW_PROCEDURE"


def test_intent_clamps_hallucinated_id_to_none(catalog):
    """Un id inventado por el modelo no puede colarse: se descarta."""
    gw = _gw(
        catalog,
        lambda kw: _json_resp(
            {"procedure_id": "tramite.que.no.existe", "confidence": 0.9, "clarification": None}
        ),
    )
    result = asyncio.run(gw.classify_intent(IntentRequest(text="algo raro")))
    assert result.procedure_id is None
    assert result.next_action == "ASK_CLARIFICATION"


def test_intent_falls_back_to_keywords_on_error(catalog):
    """Si el proveedor falla, la búsqueda no se cae: usa el mock determinista."""
    def boom(kw):
        raise RuntimeError("timeout")

    gw = _gw(catalog, boom)
    result = asyncio.run(gw.classify_intent(IntentRequest(text="quiero pedir cita para el médico")))
    assert result.procedure_id == "gva.health.primary-care.appointment"


def test_intent_refusal_falls_back(catalog):
    gw = _gw(catalog, lambda kw: _json_resp({"procedure_id": None, "confidence": 0}, "refusal"))
    result = asyncio.run(gw.classify_intent(IntentRequest(text="itv del coche")))
    # El fallback por palabras clave reconoce la ITV.
    assert result.procedure_id == "sitval.itv.appointment"


# --- Documentos (dato A2) --------------------------------------------------


def test_documents_not_sent_externally_by_default(catalog):
    """allow_documents apagado: la imagen del DNI NO va al proveedor (§13.2)."""
    gw = _gw(catalog, lambda kw: pytest.fail("no debe llamarse al proveedor"))
    result = asyncio.run(
        gw.extract_document(DocumentRequest(document_class="dni", image_base64=IMG))
    )
    # Cae al mock: datos sintéticos de demostración.
    assert result.document_class == "dni"
    assert gw._client.messages.calls == 0


def test_documents_extracted_when_enabled(catalog):
    gw = _gw(
        catalog,
        lambda kw: _json_resp(
            {"fields": [{"field": "dni_number", "value": "12345678Z", "confidence": 0.95}]}
        ),
        allow_documents=True,
    )
    result = asyncio.run(
        gw.extract_document(DocumentRequest(document_class="dni", image_base64=IMG))
    )
    assert result.fields[0].field == "dni_number"
    assert result.fields[0].value == "12345678Z"


def test_documents_degrade_to_empty_on_error(catalog):
    """Si la imagen no se lee, campos vacíos con confianza 0 (pedir repetir),
    nunca datos sintéticos presentados como reales."""
    def boom(kw):
        raise RuntimeError("ilegible")

    gw = _gw(catalog, boom, allow_documents=True)
    result = asyncio.run(
        gw.extract_document(DocumentRequest(document_class="dni", image_base64=IMG))
    )
    assert all(f.value == "" and f.confidence == 0.0 for f in result.fields)


# --- Cartas (dato A2; solo transcribe) -------------------------------------


def test_letters_not_sent_externally_by_default(catalog):
    gw = _gw(catalog, lambda kw: pytest.fail("no debe llamarse al proveedor"))
    result = asyncio.run(gw.explain_official_content(ExplainRequest(image_base64=IMG)))
    assert gw._client.messages.calls == 0
    assert result.text  # el mock devuelve una carta de ejemplo


def test_letters_transcribed_when_enabled(catalog):
    gw = _gw(
        catalog,
        lambda kw: _json_resp(
            {"text": "PROVIDENCIA DE APREMIO", "organismo": "Agencia Tributaria", "confidence": 0.9}
        ),
        allow_documents=True,
    )
    result = asyncio.run(gw.explain_official_content(ExplainRequest(image_base64=IMG)))
    assert result.text == "PROVIDENCIA DE APREMIO"
    assert result.organismo == "Agencia Tributaria"


def test_letters_degrade_on_error(catalog):
    def boom(kw):
        raise RuntimeError("ilegible")

    gw = _gw(catalog, boom, allow_documents=True)
    result = asyncio.run(gw.explain_official_content(ExplainRequest(image_base64=IMG)))
    assert result.text == ""
    assert result.confidence == 0.0


# --- Voz (Claude no hace STT) ----------------------------------------------


def test_voice_never_uses_the_provider(catalog):
    gw = _gw(catalog, lambda kw: pytest.fail("Claude no transcribe audio"), allow_documents=True)
    result = asyncio.run(gw.transcribe(AudioRequest(audio_base64=IMG)))
    assert gw._client.messages.calls == 0
    assert result.text  # frase sintética del mock
