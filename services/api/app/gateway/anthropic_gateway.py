"""Gateway de IA real sobre Claude (Anthropic), detrás del contrato ModelGateway.

Cumple la regla 11 del PRD: la lógica de negocio nunca habla con un proveedor;
todo pasa por este contrato con salidas validadas. Cambiar de proveedor es
cambiar esta clase, no los routers.

Posturas de privacidad codificadas aquí (PRD §10.4 y §13.2):

- La transcripción de voz NO usa Claude (no hace STT de audio): delega siempre
  en el fallback. No sale audio de la máquina por esta vía.
- La extracción de documentos y el OCR de cartas manejan datos A2 (imágenes de
  DNI/SIP, contenido de cartas). Enviarlos a un proveedor externo es una
  decisión con EIPD (§10.4): van detrás de `allow_documents`, DESACTIVADO por
  defecto. Mientras esté apagado, esos dos métodos usan el fallback mock.
- Ante cualquier fallo del proveedor (red, refusal, rate limit), se degrada:
  la intención cae al fallback determinista; documentos y cartas devuelven un
  resultado de baja confianza para que el kiosco pida repetir, NUNCA datos
  sintéticos presentados como reales.

Este módulo no registra jamás los valores extraídos ni el texto de las cartas.
"""

import asyncio
import json
import logging
from typing import Any

from ..catalog.models import Procedure
from .base import (
    AudioRequest,
    DocumentRequest,
    DocumentResult,
    ExplainRequest,
    ExplainResult,
    IntentRequest,
    IntentResult,
    ModelGateway,
    RawExtractedField,
    TranscriptResult,
)

logger = logging.getLogger("tramitatron.gateway")

# Campos que se piden por clase de documento. La validación determinista vive
# en app/documents/validators.py; aquí solo se leen los valores visibles.
_DOCUMENT_FIELDS: dict[str, list[str]] = {
    "dni": ["dni_number", "full_name", "birth_date"],
    "sip_card": ["sip_number", "full_name"],
}

_INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "procedure_id": {"type": ["string", "null"]},
        "confidence": {"type": "number"},
        "clarification": {"type": ["string", "null"]},
    },
    "required": ["procedure_id", "confidence", "clarification"],
    "additionalProperties": False,
}

_DOCUMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "fields": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "value": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["field", "value", "confidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["fields"],
    "additionalProperties": False,
}

_LETTER_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "organismo": {"type": ["string", "null"]},
        "confidence": {"type": "number"},
    },
    "required": ["text", "organismo", "confidence"],
    "additionalProperties": False,
}

_CLARIFICATION = {
    "es": "No he entendido qué trámite necesitas. ¿Puedes decirlo con otras palabras?",
    "ca-valencia": "No he entés quin tràmit necessites. Pots dir-ho amb altres paraules?",
}


def _clamp(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


class AnthropicModelGateway:
    """Implementación de ModelGateway con Claude.

    `fallback` es un ModelGateway (el mock) que absorbe la voz, los documentos
    y las cartas cuando no están habilitados o cuando el proveedor falla.
    `client` se inyecta en tests; en producción se crea perezosamente para no
    depender del paquete `anthropic` salvo cuando el proveedor real está activo.
    """

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        catalog: dict[str, Procedure],
        fallback: ModelGateway,
        allow_documents: bool = False,
        client: Any = None,
    ) -> None:
        self._model = model
        self._catalog = catalog
        self._fallback = fallback
        self._allow_documents = allow_documents
        if client is not None:
            self._client = client
        else:
            import anthropic  # import perezoso: solo con proveedor real

            self._client = anthropic.Anthropic(api_key=api_key)

    async def _call_json(
        self, *, system: str, content: list[dict], schema: dict, max_tokens: int
    ) -> dict:
        """Una llamada a Claude con salida JSON validada. Lanza si algo falla."""
        response = await asyncio.to_thread(
            self._client.messages.create,
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": content}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        if getattr(response, "stop_reason", None) == "refusal":
            raise RuntimeError("respuesta rechazada por el proveedor")
        text = next((b.text for b in response.content if getattr(b, "type", None) == "text"), None)
        if not text:
            raise RuntimeError("respuesta sin texto")
        return json.loads(text)

    # --- Intención (texto) --------------------------------------------------

    async def classify_intent(self, request: IntentRequest) -> IntentResult:
        catalogue = "\n".join(
            f"- {p.id}: {p.name.es}" + (f" — {p.description.es}" if p.description else "")
            for p in self._catalog.values()
        )
        system = (
            "Eres el clasificador de intención de un tótem público de trámites "
            "administrativos. Dado lo que escribe un ciudadano, elige el id del "
            "trámite más adecuado de la lista, o null si ninguno encaja con "
            "claridad. Nunca inventes un id que no esté en la lista. Devuelve la "
            "confianza (0 a 1) y, solo si el id es null, una frase breve y amable "
            f"pidiendo que lo diga con otras palabras, en el idioma '{request.language}'.\n\n"
            f"Trámites disponibles:\n{catalogue}"
        )
        try:
            data = await self._call_json(
                system=system,
                content=[{"type": "text", "text": request.text}],
                schema=_INTENT_SCHEMA,
                max_tokens=512,
            )
        except Exception as exc:  # noqa: BLE001 - degradación: la búsqueda no puede caerse
            logger.warning("classify_intent: fallback (%s)", type(exc).__name__)
            return await self._fallback.classify_intent(request)

        procedure_id = data.get("procedure_id")
        if procedure_id not in self._catalog:
            procedure_id = None
        confidence = _clamp(data.get("confidence"))
        if procedure_id is not None:
            return IntentResult(
                intent="AI_MATCH",
                confidence=confidence,
                procedure_id=procedure_id,
                next_action="SHOW_PROCEDURE",
            )
        return IntentResult(
            intent="UNKNOWN",
            confidence=confidence,
            procedure_id=None,
            next_action="ASK_CLARIFICATION",
            clarification=data.get("clarification") or _CLARIFICATION[request.language],
        )

    # --- Documentos (visión, dato A2) ---------------------------------------

    async def extract_document(self, request: DocumentRequest) -> DocumentResult:
        if not self._allow_documents:
            return await self._fallback.extract_document(request)

        wanted = _DOCUMENT_FIELDS.get(request.document_class, [])
        system = (
            "Lee los campos visibles de la imagen de un documento de identidad. "
            "Devuelve EXACTAMENTE estos campos: " + ", ".join(wanted) + ". "
            "Para cada uno, el valor tal como aparece y una confianza de 0 a 1. "
            "birth_date en formato AAAA-MM-DD. Si un campo no se ve con claridad, "
            "deja el valor vacío y la confianza en 0. No inventes datos."
        )
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": request.mime_type,
                    "data": request.image_base64,
                },
            },
            {"type": "text", "text": "Extrae los campos pedidos."},
        ]
        try:
            data = await self._call_json(
                system=system, content=content, schema=_DOCUMENT_SCHEMA, max_tokens=1024
            )
            fields = [
                RawExtractedField(
                    field=str(f["field"]),
                    value=str(f.get("value", "")),
                    confidence=_clamp(f.get("confidence")),
                )
                for f in data.get("fields", [])
                if f.get("field") in wanted
            ]
            if not fields:
                raise RuntimeError("sin campos")
            return DocumentResult(document_class=request.document_class, fields=fields)
        except Exception as exc:  # noqa: BLE001 - nunca datos sintéticos como reales
            logger.warning("extract_document: ilegible (%s)", type(exc).__name__)
            # Campos vacíos con confianza 0 => el kiosco marca revisión y pide repetir.
            return DocumentResult(
                document_class=request.document_class,
                fields=[RawExtractedField(field=f, value="", confidence=0.0) for f in wanted],
            )

    # --- Cartas (visión, dato A2; solo transcribe, ADR-004) -----------------

    async def explain_official_content(self, request: ExplainRequest) -> ExplainResult:
        if not self._allow_documents:
            return await self._fallback.explain_official_content(request)

        system = (
            "Transcribe LITERALMENTE el texto visible de esta carta administrativa. "
            "Si el organismo emisor aparece con claridad en el membrete, indícalo. "
            "No resumas, no interpretes, no valores el riesgo ni detectes plazos: "
            "solo transcribe lo que pone. Devuelve además una confianza de 0 a 1 "
            "sobre la legibilidad. Si la imagen no se lee, deja el texto vacío y la "
            "confianza en 0."
        )
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": request.mime_type,
                    "data": request.image_base64,
                },
            },
            {"type": "text", "text": "Transcribe el texto de la carta."},
        ]
        try:
            data = await self._call_json(
                system=system, content=content, schema=_LETTER_SCHEMA, max_tokens=4096
            )
            return ExplainResult(
                text=str(data.get("text", "")),
                organismo=data.get("organismo") or None,
                confidence=_clamp(data.get("confidence")),
            )
        except Exception as exc:  # noqa: BLE001 - baja confianza => el kiosco pide repetir
            logger.warning("explain_official_content: ilegible (%s)", type(exc).__name__)
            return ExplainResult(text="", organismo=None, confidence=0.0)

    # --- Voz (Claude no hace STT de audio) ----------------------------------

    async def transcribe(self, request: AudioRequest) -> TranscriptResult:
        # Claude no transcribe audio. Hasta integrar un proveedor de STT, la voz
        # sigue siendo sintética a través del fallback. No sale audio por aquí.
        return await self._fallback.transcribe(request)
