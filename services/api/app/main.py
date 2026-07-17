"""Aplicación FastAPI de Tramitatrón.

Observabilidad sin vigilancia: el log de acceso registra método, ruta y código
de estado. Nunca cuerpos de petición, query strings ni datos de sesión.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .catalog import router as catalog_router_module
from .catalog.loader import load_catalog
from .config import Settings
from .connectors import router as connectors_router_module
from .connectors.mock import MockConnector
from .documents import router as documents_router_module
from .gateway import router as gateway_router_module
from .gateway.mock import MockModelGateway
from .sessions import router as sessions_router_module
from .sessions.memory import MemorySessionStore

access_logger = logging.getLogger("tramitatron.access")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    app = FastAPI(title="Tramitatrón API", version="0.1.0")
    app.state.settings = settings
    app.state.catalog = load_catalog(settings.catalog_path)
    app.state.gateway = MockModelGateway()
    app.state.connectors = {"demo.mock": MockConnector()}

    if settings.redis_url:
        from .sessions.redis_store import RedisSessionStore

        app.state.store = RedisSessionStore(settings.redis_url, settings.session_ttl_seconds)
    else:
        app.state.store = MemorySessionStore(settings.session_ttl_seconds)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        response = await call_next(request)
        # Solo método, ruta y estado. Sin query string, sin cuerpos, sin PII.
        access_logger.info("%s %s %s", request.method, request.url.path, response.status_code)
        return response

    @app.get("/health", tags=["ops"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "tramitatron-api", "version": "0.1.0"}

    app.include_router(sessions_router_module.router)
    app.include_router(documents_router_module.router)
    app.include_router(catalog_router_module.router)
    app.include_router(gateway_router_module.router)
    app.include_router(connectors_router_module.router)
    return app


app = create_app()
