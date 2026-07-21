"""Aplicación FastAPI de Tramitatrón.

Observabilidad sin vigilancia: el log de acceso registra método, ruta y código
de estado. Nunca cuerpos de petición, query strings ni datos de sesión.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .catalog import router as catalog_router_module
from .catalog.loader import load_catalog
from .config import Settings
from .connectors import router as connectors_router_module
from .connectors.mock import MockConnector
from .connectors.worker import WorkerConnector
from .documents import router as documents_router_module
from .gateway import router as gateway_router_module
from .gateway.mock import MockModelGateway
from .knowledge import router as knowledge_router_module
from .knowledge.store import KnowledgeStore
from .letters import router as letters_router_module
from .ratelimit import RateLimiter, client_key
from .sessions import router as sessions_router_module
from .sessions.memory import MemorySessionStore
from .voice import router as voice_router_module

access_logger = logging.getLogger("tramitatron.access")
gateway_logger = logging.getLogger("tramitatron.gateway")


def _build_gateway(settings: Settings, catalog):
    """Elige el gateway de IA (PRD §10). Mock por defecto; proveedor real solo
    si hay clave. Sin clave no sale ningún dato de la máquina (regla 12)."""
    mock = MockModelGateway()
    if settings.model_provider == "anthropic" and settings.anthropic_api_key:
        from .gateway.anthropic_gateway import AnthropicModelGateway

        gateway_logger.info(
            "Gateway: Anthropic (%s); documentos externos: %s",
            settings.anthropic_model,
            "ON" if settings.allow_external_documents else "OFF (mock)",
        )
        return AnthropicModelGateway(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            catalog=catalog,
            fallback=mock,
            allow_documents=settings.allow_external_documents,
        )
    gateway_logger.info("Gateway: mock (sin proveedor de IA; nada sale de la máquina)")
    return mock


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    app = FastAPI(title="Tramitatrón API", version="0.1.0")
    app.state.settings = settings
    app.state.catalog = load_catalog(settings.catalog_path)
    app.state.knowledge = KnowledgeStore(settings.knowledge_path)
    app.state.gateway = _build_gateway(settings, app.state.catalog)
    app.state.connectors = {
        "demo.mock": MockConnector(),
        # Trámite de demostración por navegación asistida (worker Playwright).
        # Si no hay worker configurado, responde "no disponible" sin romperse.
        "connectors.worker.demo": WorkerConnector(
            name="connectors.worker.demo",
            worker_url=settings.browser_worker_url,
            worker_connector="demo.worker.appointment",
        ),
    }

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

    app.state.rate_limiter = RateLimiter(
        settings.rate_limit_requests, settings.rate_limit_window_seconds
    )

    @app.middleware("http")
    async def rate_limit(request: Request, call_next):
        # El liveness no se limita: debe responder siempre.
        limiter: RateLimiter = app.state.rate_limiter
        if request.url.path != "/health":
            allowed, retry_after = limiter.check(client_key(request))
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Demasiadas peticiones. Inténtalo en un momento."},
                    headers={"Retry-After": str(int(retry_after) + 1)},
                )
        return await call_next(request)

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
    app.include_router(letters_router_module.router)
    app.include_router(voice_router_module.router)
    app.include_router(catalog_router_module.router)
    app.include_router(gateway_router_module.router)
    app.include_router(knowledge_router_module.router)
    app.include_router(connectors_router_module.router)
    return app


app = create_app()
