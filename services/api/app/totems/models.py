"""Modelos del registro de tótems (TT-601).

Un tótem es un DISPOSITIVO, no una persona: su id, municipio, ubicación,
versión y salud de periféricos son datos OPERATIVOS no identificativos (PRD
§9.2, clasificación A0). Aquí no hay nada de la ciudadanía; el latido nunca
lleva sesiones, textos, imágenes ni audio.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Formato del identificador de tótem (kebab con puntos permitidos), p. ej.
# "cyl-valladolid-01". Vale tanto para el cuerpo como para la ruta.
TOTEM_ID_PATTERN = r"^[a-z0-9][a-z0-9._-]{1,63}$"

PeripheralState = Literal["ok", "down", "unknown"]
# Estado derivado del tótem según su último latido y sus periféricos.
TotemState = Literal["online", "degraded", "offline", "unknown"]


class Peripherals(BaseModel):
    model_config = ConfigDict(extra="forbid")

    camera: PeripheralState = "unknown"
    scanner: PeripheralState = "unknown"
    printer: PeripheralState = "unknown"
    paper_level: int = Field(default=100, ge=0, le=100)


class HeartbeatRequest(BaseModel):
    """Lo que un tótem envía en cada latido. Estricto y sin PII."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(pattern=r"^[\w.\-+]{1,40}$")
    peripherals: Peripherals = Field(default_factory=Peripherals)


class TotemStatus(BaseModel):
    id: str
    label: str | None
    municipality: str | None
    state: TotemState
    version: str | None
    peripherals: Peripherals | None
    last_seen: str | None
    seconds_since_seen: float | None
    # En el parque declarado (infra/totems.yaml).
    declared: bool
    # Reportó un latido sin estar declarado (alta automática).
    auto_registered: bool


class FleetSummary(BaseModel):
    total: int
    online: int
    degraded: int
    offline: int
    unknown: int


class FleetView(BaseModel):
    generated_at: str
    offline_after_seconds: float
    summary: FleetSummary
    totems: list[TotemStatus]
