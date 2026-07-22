"""Canal de voz: transcripción para revisión humana (PRD §14.3).

Diferencia importante con documentos y cartas: aquí NO se guarda nada en la
sesión. El audio se decodifica, se transcribe y se descarta dentro de la misma
petición; la transcripción se devuelve al kiosco y vive solo en la memoria del
navegador hasta que la persona la confirma o la borra.

Motivo: "audio bruto" y "texto libre" son datos que el PRD §13.2 prohíbe
persistir, y E2E-01 exige que al cerrar la sesión no quede ninguno de los dos.
La forma más sencilla de garantizarlo es no escribirlos nunca.

La transcripción tampoco se usa para actuar: el kiosco la muestra y espera
confirmación explícita antes de pasarla al clasificador de intención.
"""

import base64
import binascii

from fastapi import APIRouter, HTTPException, Request

from ..documents.router import _get_session_or_404
from ..gateway.base import AudioRequest, ModelGateway
from .models import (
    MAX_AUDIO_BYTES,
    MIN_TRANSCRIPTION_CONFIDENCE,
    TranscribeRequest,
    TranscribeResponse,
)

router = APIRouter(prefix="/api/session/{session_id}/voice", tags=["voice"])


def _quality_check(audio_base64: str) -> None:
    try:
        decoded = base64.b64decode(audio_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Audio ilegible (base64 inválido)") from exc
    if not decoded:
        raise HTTPException(status_code=400, detail="Audio vacío")
    if len(decoded) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio demasiado largo")


@router.post("/transcribe")
async def transcribe(
    session_id: str, body: TranscribeRequest, request: Request
) -> TranscribeResponse:
    # La sesión debe existir: la voz es un canal de una sesión viva, no un
    # servicio abierto de transcripción.
    _get_session_or_404(request, session_id)
    _quality_check(body.audio_base64)
    request.app.state.metrics.record_channel("voice")

    gateway: ModelGateway = request.app.state.gateway
    result = await gateway.transcribe(
        AudioRequest(
            audio_base64=body.audio_base64,
            mime_type=body.mime_type,
            language=body.language,
        )
    )

    # Ni el audio ni el texto se escriben en la sesión: salen en la respuesta
    # y desaparecen de la API al terminar esta función.
    return TranscribeResponse(
        text=result.text,
        confidence=result.confidence,
        usable=result.confidence >= MIN_TRANSCRIPTION_CONFIDENCE and bool(result.text.strip()),
    )
