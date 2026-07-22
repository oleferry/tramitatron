"""Explicación de cartas administrativas (TT-404, PRD §5.2 caso D).

Pipeline: CAPTURE → QUALITY_CHECK → TRANSCRIBE (gateway) → ASSESS
(determinista) → EXPLAIN (plantillas) → PURGE.

El texto transcrito vive dentro de la sesión, igual que las extracciones de
documentos: hereda su TTL y su purga. Ni la imagen ni el texto se escriben en
disco ni en logs. La respuesta separa hechos de explicación y nunca sugiere
una actuación jurídica concreta.
"""

import uuid

from fastapi import APIRouter, HTTPException, Request, Response

from ..documents.router import _get_session_or_404, _quality_check, _store
from ..gateway.base import ExplainRequest, ModelGateway
from . import wording
from .analysis import assess
from .models import LetterAnalysis, LetterExplanation, LetterFacts, UploadLetterRequest

router = APIRouter(prefix="/api/session/{session_id}/letters", tags=["letters"])

_LETTER_KEY_PREFIX = "letter_"
_EXCERPT_MAX_CHARS = 400
# Por debajo de esta confianza no se explica nada: se pide repetir la foto.
# Explicar mal una carta de embargo es peor que admitir que no se ha leído.
_MIN_TRANSCRIPTION_CONFIDENCE = 0.55


def _excerpt(text: str) -> str:
    clean = " ".join(text.split())
    if len(clean) <= _EXCERPT_MAX_CHARS:
        return clean
    cut = clean[:_EXCERPT_MAX_CHARS]
    last_stop = cut.rfind(". ")
    return (cut[: last_stop + 1] if last_stop > 120 else cut) + "…"


@router.post("", status_code=201)
async def explain_letter(
    session_id: str, body: UploadLetterRequest, request: Request
) -> LetterAnalysis:
    _get_session_or_404(request, session_id)
    _quality_check(body.image_base64)
    request.app.state.metrics.record_channel("letters")

    gateway: ModelGateway = request.app.state.gateway
    transcript = await gateway.explain_official_content(
        ExplainRequest(
            image_base64=body.image_base64,
            mime_type=body.mime_type,
            language=body.language,
        )
    )

    letter_id = uuid.uuid4().hex[:12]

    # Transcripción pobre: no se interpreta, se pide repetir la foto.
    if transcript.confidence < _MIN_TRANSCRIPTION_CONFIDENCE or not transcript.text.strip():
        return LetterAnalysis(
            letter_id=letter_id,
            transcription_confidence=transcript.confidence,
            facts=LetterFacts(excerpt=""),
            explanation=LetterExplanation(
                summary=wording.unreadable_summary(body.language),
                risk_level="normal",
                recommend_human=True,
                human_advice=wording.HUMAN_ADVICE[body.language],
                disclaimer=wording.DISCLAIMER[body.language],
            ),
        )

    analysis = assess(transcript.text)
    if transcript.organismo and not analysis["organismo"]:
        analysis["organismo"] = transcript.organismo

    result = LetterAnalysis(
        letter_id=letter_id,
        transcription_confidence=transcript.confidence,
        facts=LetterFacts(
            organismo=analysis["organismo"],
            deadlines=analysis["deadlines"],
            sensitive_data=analysis["sensitive_data"],
            excerpt=_excerpt(transcript.text),
        ),
        explanation=LetterExplanation(
            summary=wording.build_summary(body.language, analysis),
            risk_level=analysis["risk_level"],
            risk_terms=analysis["risk_terms"],
            ambiguous_deadline=analysis["ambiguous_deadline"],
            recommend_human=analysis["recommend_human"],
            human_advice=(
                wording.HUMAN_ADVICE[body.language] if analysis["recommend_human"] else None
            ),
            disclaimer=wording.DISCLAIMER[body.language],
        ),
    )

    # El análisis vive dentro de la sesión: mismo TTL, misma purga.
    _store(request).set_data(
        session_id, _LETTER_KEY_PREFIX + letter_id, result.model_dump_json()
    )
    return result


@router.get("/{letter_id}")
def get_letter(session_id: str, letter_id: str, request: Request) -> LetterAnalysis:
    session = _get_session_or_404(request, session_id)
    raw = session.data.get(_LETTER_KEY_PREFIX + letter_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="Carta no encontrada en la sesión")
    return LetterAnalysis.model_validate_json(raw)


@router.delete("/{letter_id}", status_code=204)
def purge_letter(session_id: str, letter_id: str, request: Request) -> Response:
    _get_session_or_404(request, session_id)
    _store(request).remove_data(session_id, _LETTER_KEY_PREFIX + letter_id)
    return Response(status_code=204)
