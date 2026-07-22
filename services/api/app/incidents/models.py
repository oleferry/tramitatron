"""Modelos de incidencias (TT-603, PRD §13.3 tabla `incidents`).

Sin campos personales: código anónimo, componente, conector, severidad,
error técnico REDACTADO, marcas de tiempo y resolución. El id de tótem es dato
del dispositivo (A0), no de la persona.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..totems.models import TOTEM_ID_PATTERN

# Severidades operativas (PRD §19.2).
Severity = Literal["S1", "S2", "S3", "S4"]
# Ciclo de vida de la incidencia.
IncidentStatus = Literal["open", "acknowledged", "resolved"]
# Componente afectado. Conjunto cerrado para que el panel agregue con sentido.
Component = Literal[
    "api",
    "backend",
    "connector",
    "gateway",
    "knowledge",
    "printer",
    "camera",
    "scanner",
    "network",
    "kiosk",
]


class IncidentReport(BaseModel):
    """Lo que se reporta al abrir una incidencia. Estricto y sin PII conocida."""

    model_config = ConfigDict(extra="forbid")

    component: Component
    severity: Severity = "S3"
    # Se REDACTA siempre antes de guardar (redact.py). El cliente no debe mandar
    # PII, pero si la manda, no se persiste.
    technical_error: str = Field(default="", max_length=2000)
    connector: str | None = Field(default=None, max_length=80)
    totem_id: str | None = Field(default=None, pattern=TOTEM_ID_PATTERN)


class Incident(BaseModel):
    code: str
    component: Component
    connector: str | None
    severity: Severity
    technical_error: str
    totem_id: str | None
    status: IncidentStatus
    created_at: str
    updated_at: str
    resolution: str | None


class IncidentSummary(BaseModel):
    total: int
    open: int
    by_severity: dict[str, int]


class ResolveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str = Field(default="", max_length=500)
