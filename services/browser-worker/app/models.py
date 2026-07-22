"""Modelos del worker de navegación asistida (PRD §12.3, TT-502).

El worker NUNCA devuelve "completed": su resultado terminal es siempre
`user_handoff`. Prepara el trámite (navega y rellena los campos seguros) y
cede el control a la persona para el CAPTCHA, la autenticación y la
confirmación final (regla 5 del §30). No reserva nada por su cuenta.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StepKind = Literal["navigate", "read", "fill", "advance", "handoff", "error"]
PrepareStatus = Literal["user_handoff", "unavailable", "error"]


class PrepareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connector: str
    # Campos seguros a precompletar (matrícula, tipo de vehículo…). NUNCA
    # credenciales, CAPTCHA ni datos de firma: el worker los ignora aunque
    # lleguen.
    fields: dict[str, str] = Field(default_factory=dict)
    language: Literal["es", "ca-valencia"] = "es"


class StepEvent(BaseModel):
    """Un paso trazable de la navegación, para auditoría y para la interfaz."""

    kind: StepKind
    detail: str


class PrepareResult(BaseModel):
    status: PrepareStatus
    connector: str
    # URL oficial donde la persona continúa el trámite.
    url: str | None = None
    # Campos que el worker ha dejado precompletados.
    prefilled: list[str] = Field(default_factory=list)
    # Lo que la persona debe hacer a mano (p. ej. "captcha", "confirmar").
    pending: list[str] = Field(default_factory=list)
    events: list[StepEvent] = Field(default_factory=list)
    message: str | None = None


class HealthResult(BaseModel):
    connector: str
    healthy: bool
    detail: str | None = None
