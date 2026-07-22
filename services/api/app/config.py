"""Configuración de la API. Todo llega por variables de entorno; sin secretos en código."""

import os
from dataclasses import dataclass, field
from pathlib import Path

# Raíz del repo: services/api/app/config.py -> tres niveles arriba. En la
# imagen Docker el árbol es más corto (/srv/app); ahí las rutas llegan por
# variables de entorno y el fallback solo evita un IndexError en el import.
# Versión desplegada de la API (PRD §18.1 Operación, TT-604). Una constante por
# ahora; en su día vendrá del pipeline de release.
APP_VERSION = "0.1.0"

_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[3] if len(_HERE.parents) > 3 else _HERE.parents[-1]
_DEFAULT_CATALOG = _REPO_ROOT / "connectors" / "catalog"
_DEFAULT_KNOWLEDGE = _REPO_ROOT / "knowledge"
_DEFAULT_TOTEMS = _REPO_ROOT / "infra" / "totems.yaml"


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

    # Token del panel institucional (TT-602/TT-601). Si se define, la LECTURA del
    # cuadro de mando (KPIs y salud de tótems) exige `Authorization: Bearer
    # <token>`. Sin definir, el panel queda abierto (demo local); no contiene PII,
    # solo agregados y datos operativos del dispositivo. La ingesta de eventos del
    # kiosco y los latidos de tótem son siempre públicos.
    admin_token: str | None = field(default_factory=lambda: os.getenv("ADMIN_TOKEN") or None)

    # Registro de tótems (TT-601). Parque declarado (opcional) y política de
    # latido. `TOTEM_TOKEN`, si se define, exige `X-Totem-Token` en el latido
    # (como el device-agent). La ventana sin latido tras la que un tótem se marca
    # «offline» (por defecto 180 s: tres latidos de 60 s perdidos).
    totems_path: Path = field(
        default_factory=lambda: Path(os.getenv("TOTEMS_PATH", str(_DEFAULT_TOTEMS)))
    )
    totem_token: str | None = field(default_factory=lambda: os.getenv("TOTEM_TOKEN") or None)
    totem_offline_after_seconds: float = field(
        default_factory=lambda: float(os.getenv("TOTEM_OFFLINE_AFTER_SECONDS", "180"))
    )
