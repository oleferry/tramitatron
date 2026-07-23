"""Worker de navegación asistida (servicio separado, PRD §9.3 y regla 8).

Prepara trámites en portales de la allowlist y cede a la persona en el CAPTCHA,
la identificación y la confirmación. Nunca reserva ni envía formularios.
"""

import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException

from . import worker
from .config import Settings
from .drivers.base import BrowserDriver
from .drivers.simulated import SimulatedDriver
from .models import HealthResult, PrepareRequest, PrepareResult
from .portal import router as portal_router
from .registry import build_registry

logger = logging.getLogger("tramitatron.worker")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        await app.state.http_client.aclose()

    app = FastAPI(title="Tramitatrón Browser Worker", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.registry = build_registry(settings.portal_authority)

    # El driver simulado navega el portal de pruebas por transporte ASGI (mismo
    # proceso, sin red). El de Playwright necesita el portal servido de verdad.
    app.state.http_client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url=f"http://{settings.portal_authority}",
    )

    async def make_driver() -> BrowserDriver:
        if settings.driver == "playwright":
            from .drivers.playwright_driver import PlaywrightDriver

            return await PlaywrightDriver.launch()
        return SimulatedDriver(app.state.http_client)

    app.state.make_driver = make_driver

    app.include_router(portal_router)

    @app.get("/worker/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "driver": settings.driver}

    @app.post("/worker/prepare", tags=["worker"])
    async def prepare(body: PrepareRequest) -> PrepareResult:
        spec = app.state.registry.get(body.connector)
        if spec is None:
            raise HTTPException(status_code=404, detail="Conector desconocido")
        return await worker.prepare(
            spec,
            body.fields,
            app.state.make_driver,
            settings.timeout_seconds,
            confirm=body.confirm,
        )

    @app.post("/worker/healthcheck/{connector}", tags=["worker"])
    async def healthcheck(connector: str) -> HealthResult:
        spec = app.state.registry.get(connector)
        if spec is None:
            raise HTTPException(status_code=404, detail="Conector desconocido")
        return await worker.healthcheck(spec, app.state.make_driver, settings.timeout_seconds)

    return app


app = create_app()
