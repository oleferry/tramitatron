"""Modelo declarativo del catálogo de trámites (PRD §12.1).

Cada trámite se define en un YAML de `connectors/catalog/` y se valida aquí.
Un YAML inválido debe impedir el arranque: mejor fallar que mostrar un trámite
mal definido a un ciudadano.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

ExecutionMode = Literal["information", "assisted", "integrated", "referral"]
RiskClass = Literal["A0", "A1", "A2", "A3"]
ProcedureStatus = Literal["available", "coming_soon", "disabled"]


class LocalizedText(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    es: str
    ca_valencia: str = Field(alias="ca-valencia")


class ConnectorRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["mock", "playwright", "api"]
    package: str


class HealthcheckSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cadence: Literal["daily", "weekly", "hourly"]
    synthetic_data_only: bool = True


class Procedure(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9_.-]+$")
    name: LocalizedText
    description: LocalizedText | None = None
    territory: str
    execution_mode: ExecutionMode
    risk_class: RiskClass
    status: ProcedureStatus = "available"
    official_sources: list[HttpUrl] = []
    required_fields: list[str] = []
    requirements: list[LocalizedText] = []
    confirmation_required: bool = True
    captcha_policy: Literal["user_only"] = "user_only"
    document_retention: Literal["none"] = "none"
    connector: ConnectorRef
    healthcheck: HealthcheckSpec | None = None


class CatalogSummaryItem(BaseModel):
    """Proyección ligera para la pantalla de catálogo del kiosco."""

    id: str
    name: LocalizedText
    description: LocalizedText | None
    status: ProcedureStatus
    execution_mode: ExecutionMode
