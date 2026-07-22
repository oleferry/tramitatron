"""Modelos de entrada del panel (TT-602). Estrictos: nada de texto libre."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Solo el kiosco puede señalar estos dos hitos de UI; los demás (completado,
# derivación, fallo) los registra el servidor al ejecutar el trámite, que es la
# fuente autoritativa. Aquí no se aceptan "completed"/"failed" desde fuera.
UiProcedureEvent = Literal["started", "abandoned"]


class ProcedureEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: UiProcedureEvent
    # Se valida contra el catálogo en el router; aquí solo forma.
    procedure_id: str = Field(pattern=r"^[a-z0-9._-]{1,80}$")


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: int = Field(ge=1, le=5)
    # Opcional: a qué trámite se refiere la valoración (no obligatorio).
    procedure_id: str | None = Field(default=None, pattern=r"^[a-z0-9._-]{1,80}$")
