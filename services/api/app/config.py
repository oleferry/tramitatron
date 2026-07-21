"""Configuración de la API. Todo llega por variables de entorno; sin secretos en código."""

import os
from dataclasses import dataclass, field
from pathlib import Path

# Raíz del repo: services/api/app/config.py -> tres niveles arriba. En la
# imagen Docker el árbol es más corto (/srv/app); ahí las rutas llegan por
# variables de entorno y el fallback solo evita un IndexError en el import.
_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[3] if len(_HERE.parents) > 3 else _HERE.parents[-1]
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

    # --- Gateway de IA (PRD §10) --------------------------------------------
    # Sin clave, el proveedor es "mock" y no sale ningún dato de la máquina
    # (regla 12). Con ANTHROPIC_API_KEY presente se activa el proveedor real,
    # salvo que MODEL_PROVIDER lo fuerce.
    anthropic_api_key: str | None = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY") or None
    )
    model_provider: str = field(
        default_factory=lambda: os.getenv("MODEL_PROVIDER")
        or ("anthropic" if os.getenv("ANTHROPIC_API_KEY") else "mock")
    )
    anthropic_model: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8")
    )
    # Enviar imágenes de documentos y cartas (datos A2, PRD §13.2) a un
    # proveedor externo requiere una decisión de arquitectura y EIPD (§10.4).
    # Por eso va detrás de su propio interruptor y está DESACTIVADO por defecto:
    # con el proveedor real, la extracción de DNI/SIP y el OCR de cartas siguen
    # siendo mock hasta que un operador lo habilite explícitamente.
    allow_external_documents: bool = field(
        default_factory=lambda: os.getenv("ANTHROPIC_ALLOW_DOCUMENTS", "").strip().lower()
        in {"1", "true", "yes", "si", "sí"}
    )
