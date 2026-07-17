"""Modelos del servicio documental efímero (PRD §11).

Cada campo extraído lleva valor, confianza, validador y estado (PRD §11.5).
La extracción vive DENTRO de los datos de la sesión: expira y se purga con ella.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DocumentClass = Literal["dni", "sip_card"]
FieldStatus = Literal["VALID", "REVIEW_REQUIRED", "INVALID"]

# Umbral de confianza por debajo del cual un campo exige revisión explícita.
REVIEW_CONFIDENCE_THRESHOLD = 0.80

# Tamaño máximo de imagen aceptado (base64 decodificado), 8 MB.
MAX_IMAGE_BYTES = 8 * 1024 * 1024


class UploadDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_class: DocumentClass
    image_base64: str = Field(min_length=1)
    mime_type: Literal["image/png", "image/jpeg"] = "image/png"


class ExtractedField(BaseModel):
    field: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    validator: str
    status: FieldStatus


class DocumentExtraction(BaseModel):
    document_id: str
    document_class: DocumentClass
    fields: list[ExtractedField]


class ConfirmDocumentRequest(BaseModel):
    """Valores revisados (y corregidos si hacía falta) por el ciudadano."""

    model_config = ConfigDict(extra="forbid")

    fields: dict[str, str] = Field(min_length=1)


class ConfirmDocumentResponse(BaseModel):
    accepted: bool
    # Estado final por campo tras validación determinista.
    fields: list[ExtractedField]
