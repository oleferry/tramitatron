"""Gateway multimodelo (PRD §10). La lógica de negocio nunca habla con un
proveedor de IA directamente: siempre a través de este contrato, con salidas
estructuradas y validadas. En el hito 1 solo existe la implementación mock."""

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

NextAction = Literal["SHOW_PROCEDURE", "ASK_CLARIFICATION", "REFER_TO_HUMAN"]


class IntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=500)
    language: Literal["es", "ca-valencia"] = "es"


class IntentResult(BaseModel):
    intent: str
    confidence: float = Field(ge=0.0, le=1.0)
    procedure_id: str | None = None
    next_action: NextAction
    clarification: str | None = None


class DocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_class: Literal["dni", "sip_card"]
    image_base64: str
    mime_type: str = "image/png"
    language: Literal["es", "ca-valencia"] = "es"


class RawExtractedField(BaseModel):
    field: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)


class DocumentResult(BaseModel):
    document_class: str
    fields: list[RawExtractedField]


class ModelGateway(Protocol):
    async def classify_intent(self, request: IntentRequest) -> IntentResult: ...

    async def extract_document(self, request: DocumentRequest) -> DocumentResult: ...
