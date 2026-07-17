"""Modelos del conocimiento oficial (PRD §16 y tabla knowledge_sources §13.3)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class KnowledgeSource(BaseModel):
    """Entrada de la allowlist knowledge/sources.yaml."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9-]+$")
    url: HttpUrl
    organismo: str
    title: str
    territory: str
    procedure_ids: list[str] = []
    review_cadence: Literal["daily", "weekly", "monthly"]


class SnapshotMeta(BaseModel):
    """Estado de la última captura de una fuente (index.json de snapshots)."""

    source_id: str
    fetched_at: str  # ISO 8601
    sha256: str
    status: Literal["ok", "error"]
    text_file: str | None = None
    error: str | None = None


class SourceStatus(BaseModel):
    """Proyección para el endpoint de estado (futuro panel institucional)."""

    id: str
    organismo: str
    title: str
    url: str
    review_cadence: str
    snapshot_status: Literal["ok", "error", "pending"]
    fetched_at: str | None = None


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=500)
    language: Literal["es", "ca-valencia"] = "es"
    procedure_id: str | None = None


class SourceInfo(BaseModel):
    organismo: str
    title: str
    url: str
    fetched_at: str


class AskResponse(BaseModel):
    found: bool
    # Extracto literal de la fuente oficial; nunca texto generado sin fuente.
    answer: str | None = None
    source: SourceInfo | None = None
