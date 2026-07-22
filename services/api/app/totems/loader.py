"""Carga del parque de tótems declarado (infra/totems.yaml).

El fichero es OPCIONAL: sin él, el registro arranca vacío y los tótems se dan
de alta solos con su primer latido. Con él, el panel muestra el parque esperado
y marca como «offline» los tótems declarados que aún no han reportado.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .models import TOTEM_ID_PATTERN


class TotemRegistryError(Exception):
    pass


class DeclaredTotem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=TOTEM_ID_PATTERN)
    label: str | None = None
    municipality: str | None = None


def load_totems(path: Path) -> list[DeclaredTotem]:
    if not path.is_file():
        return []

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = raw.get("totems", []) if isinstance(raw, dict) else []

    result: list[DeclaredTotem] = []
    seen: set[str] = set()
    for item in items:
        try:
            totem = DeclaredTotem.model_validate(item)
        except Exception as exc:
            raise TotemRegistryError(f"Tótem inválido en {path.name}: {exc}") from exc
        if totem.id in seen:
            raise TotemRegistryError(f"Id de tótem duplicado: {totem.id}")
        seen.add(totem.id)
        result.append(totem)
    return result
