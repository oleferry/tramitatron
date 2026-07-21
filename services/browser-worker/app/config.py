"""Configuración del worker. Todo por variables de entorno; sin secretos."""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    # "simulated" (httpx contra el portal local, por defecto) o "playwright".
    driver: str = field(default_factory=lambda: os.getenv("BROWSER_DRIVER", "simulated"))
    # Autoridad del portal de pruebas. Con el driver simulado/tests basta un
    # host lógico (transporte ASGI). Con Playwright, un host:port real servido
    # por uvicorn, p. ej. "127.0.0.1:8220".
    portal_authority: str = field(default_factory=lambda: os.getenv("PORTAL_HOST", "worker.local"))
    timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("WORKER_TIMEOUT_SECONDS", "20"))
    )
