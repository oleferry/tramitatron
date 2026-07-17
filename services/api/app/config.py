"""Configuración de la API. Todo llega por variables de entorno; sin secretos en código."""

import os
from dataclasses import dataclass, field
from pathlib import Path

# Raíz del repo: services/api/app/config.py -> tres niveles arriba
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CATALOG = _REPO_ROOT / "connectors" / "catalog"
_DEFAULT_KNOWLEDGE = _REPO_ROOT / "knowledge"


@dataclass(frozen=True)
class Settings:
    session_ttl_seconds: float = field(
        default_factory=lambda: float(os.getenv("SESSION_TTL_SECONDS", "1200"))
    )
    redis_url: str | None = field(default_factory=lambda: os.getenv("REDIS_URL") or None)
    catalog_path: Path = field(
        default_factory=lambda: Path(os.getenv("CATALOG_PATH", str(_DEFAULT_CATALOG)))
    )
    knowledge_path: Path = field(
        default_factory=lambda: Path(os.getenv("KNOWLEDGE_PATH", str(_DEFAULT_KNOWLEDGE)))
    )
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            o.strip()
            for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
            if o.strip()
        )
    )
