"""Modelos del explicador de cartas (TT-404).

La respuesta separa SIEMPRE dos bloques (PRD §5.2 caso D): `facts`, que son
datos leídos literalmente del documento, y `explanation`, que es la lectura
del sistema. El ciudadano debe poder distinguir qué pone la carta de qué
opina el asistente.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Una carta ocupa más que un DNI, pero sigue habiendo un límite duro.
MAX_LETTER_BYTES = 8 * 1024 * 1024

RiskLevel = Literal["normal", "high"]


class UploadLetterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image_base64: str
    mime_type: str = "image/png"
    language: Literal["es", "ca-valencia"] = "es"


class LetterFacts(BaseModel):
    """Hechos leídos del documento, sin interpretación."""

    organismo: str | None = None
    deadlines: list[str] = []
    # Tipos de dato sensible detectados (p. ej. "dni", "iban"). Nunca el valor.
    sensitive_data: list[str] = []
    excerpt: str


class LetterExplanation(BaseModel):
    """Lectura del sistema. Nunca contiene consejo jurídico concreto."""

    summary: str
    risk_level: RiskLevel
    risk_terms: list[str] = []
    ambiguous_deadline: bool = False
    recommend_human: bool
    human_advice: str | None = None
    disclaimer: str


class LetterAnalysis(BaseModel):
    letter_id: str
    transcription_confidence: float = Field(ge=0.0, le=1.0)
    facts: LetterFacts
    explanation: LetterExplanation
