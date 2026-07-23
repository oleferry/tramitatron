"""Modelos del worker de navegación asistida (PRD §12.3, TT-502).

Para trámites de ALTO nivel de identificación (Cl@ve/firma) el worker prepara y
cede: su resultado terminal es `user_handoff` y nunca envía (regla 5 del §30).

Para trámites REVERSIBLES sin Cl@ve —una cita del médico o de Hacienda, que se
identifican con el CIP de la tarjeta o el NIF y se pueden anular— el worker SÍ
puede COMPLETAR, pero solo cuando llega el flag `confirm` (el "Sí, confirma"
explícito del ciudadano). Sin ese flag, prepara y cede igual. Nunca automatiza
un CAPTCHA ni una firma: eso sigue siendo de la persona.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StepKind = Literal["navigate", "read", "fill", "advance", "handoff", "error"]
PrepareStatus = Literal["completed", "user_handoff", "unavailable", "error"]


class PrepareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connector: str
    # Campos seguros a precompletar (CIP, apellido, centro, fecha…). NUNCA
    # credenciales, CAPTCHA ni datos de firma: el worker los ignora aunque
    # lleguen.
    fields: dict[str, str] = Field(default_factory=dict)
    # Confirmación EXPLÍCITA del ciudadano ("Sí, confirma mi cita"). Solo con
    # esto —y solo si el conector es `completable`— el worker envía el formulario
    # final. Por defecto False: preparar y ceder.
    confirm: bool = False
    language: Literal["es", "ca-valencia"] = "es"


class StepEvent(BaseModel):
    """Un paso trazable de la navegación, para auditoría y para la interfaz."""

    kind: StepKind
    detail: str


class PrepareResult(BaseModel):
    status: PrepareStatus
    connector: str
    # URL oficial donde la persona continúa (handoff) o donde quedó la cita
    # (completed).
    url: str | None = None
    # Campos que el worker ha dejado precompletados.
    prefilled: list[str] = Field(default_factory=list)
    # Lo que la persona debe hacer a mano (p. ej. "captcha", "confirmar").
    pending: list[str] = Field(default_factory=list)
    # Referencia/justificante de la cita cuando el trámite se completa.
    reference: str | None = None
    events: list[StepEvent] = Field(default_factory=list)
    message: str | None = None


class HealthResult(BaseModel):
    connector: str
    healthy: bool
    detail: str | None = None
