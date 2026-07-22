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


def _anthropic_key() -> str | None:
    """Clave de Anthropic: nombre propio del proyecto primero, estándar después."""
    return os.getenv("TRAMITATRON_ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or None


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
    # (regla 12). Con la clave presente se activa el proveedor real, salvo que
    # MODEL_PROVIDER lo fuerce. La clave se lee de TRAMITATRON_ANTHROPIC_API_KEY
    # (nombre propio del proyecto, para no mezclar claves de varios proyectos) y,
    # como respaldo, de ANTHROPIC_API_KEY. Ojo: separar el gasto por proyecto se
    # consigue usando una CLAVE distinta por proyecto (Anthropic factura por
    # clave), no por el nombre de la variable.
    anthropic_api_key: str | None = field(default_factory=lambda: _anthropic_key())
    model_provider: str = field(
        default_factory=lambda: os.getenv("MODEL_PROVIDER")
        or ("anthropic" if _anthropic_key() else "mock")
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

    # URL del worker de navegación asistida (servicio separado, PRD §9.3). Sin
    # ella, los trámites por navegador responden "no disponible" con un mensaje
    # claro, en vez de romperse.
    browser_worker_url: str | None = field(
        default_factory=lambda: os.getenv("BROWSER_WORKER_URL") or None
    )

    # Límite de peticiones por cliente y ventana (ENS mp.s.2, threat model D4).
    # Generoso para un tótem normal; frena una inundación. 0 desactiva el límite.
    rate_limit_requests: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_REQUESTS", "240"))
    )
    rate_limit_window_seconds: float = field(
        default_factory=lambda: float(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    )

    # Token del panel institucional (TT-602). Si se define, la LECTURA del cuadro
    # de mando exige `Authorization: Bearer <token>`. Sin definir, el panel queda
    # abierto (demo local); no contiene PII, solo agregados. La ingesta de
    # eventos del kiosco es siempre pública (el kiosco es anónimo).
    admin_token: str | None = field(default_factory=lambda: os.getenv("ADMIN_TOKEN") or None)
