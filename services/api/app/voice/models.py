"""Modelos del canal de voz (PRD §14.3).

El audio bruto y el texto libre están en la lista de datos que NO pueden
persistir (PRD §13.2, y E2E-01: "no queda audio, texto libre ni PII"). Por eso
aquí no hay ningún modelo de almacenamiento: solo petición y respuesta.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Un turno de voz es corto por diseño (PRD §14.3: "textos breves"). El límite
# evita además que una grabación accidental larga viaje al servidor.
MAX_AUDIO_BYTES = 4 * 1024 * 1024

# Por debajo de esta confianza no se ofrece usar el texto: se pide repetir.
MIN_TRANSCRIPTION_CONFIDENCE = 0.60


class TranscribeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audio_base64: str
    mime_type: str = "audio/webm"
    language: Literal["es", "ca-valencia"] = "es"


class TranscribeResponse(BaseModel):
    """Transcripción para revisar en pantalla, nunca para actuar sin confirmar.

    `usable` en falso significa "no te fíes de esto, repite": la interfaz
    ofrece volver a grabar en lugar del botón de confirmar.
    """

    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    usable: bool
