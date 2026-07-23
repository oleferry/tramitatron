"""Agente local de periféricos del tótem — MODO SIMULADOR (TT-401).

En el hito 1 no hay hardware: la impresora escribe ficheros de texto en un
directorio de spool local y la cámara devuelve una imagen sintética fija.
El agente solo debe escuchar en localhost (PRD §17.2); nunca se expone a red.

Autenticación al frontend (ENS op.acc, threat model S2): si se define
DEVICE_AGENT_TOKEN, las operaciones (imprimir, capturar, purgar) exigen la
cabecera `X-Device-Token`. Así, aunque el agente esté en localhost, solo el
frontend del tótem —que conoce el token— puede accionar los periféricos, no
cualquier otro proceso local. El healthcheck queda abierto para el liveness.
"""

import base64
import os
import secrets
import shutil
import time
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

SPOOL_DIR = Path(__file__).resolve().parents[1] / "spool"

# PNG gris de 1x1 px: sustituto sintético de una captura de cámara.
_FAKE_CAPTURE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNiAAAABgADNjd8qAAAAABJRU5ErkJggg=="
)


class PrintRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lines: list[str] = Field(min_length=1, max_length=40)


def create_app(device_token: str | None = None) -> FastAPI:
    # Sin argumento, el token llega por entorno. Sin token, el agente queda
    # abierto (solo apto para desarrollo en localhost).
    token = device_token if device_token is not None else (os.getenv("DEVICE_AGENT_TOKEN") or None)

    app = FastAPI(title="Tramitatrón Device Agent (simulador)", version="0.1.0")
    app.state.device_token = token

    async def require_token(x_device_token: str | None = Header(default=None)) -> None:
        if token is None:
            return
        # Comparación en tiempo constante para no filtrar el token por timing.
        if x_device_token is None or not secrets.compare_digest(x_device_token, token):
            raise HTTPException(status_code=401, detail="Token de dispositivo inválido o ausente")

    @app.get("/device/health")
    def health() -> dict:
        return {
            "status": "ok",
            "mode": "simulator",
            "camera": "simulated",
            "scanner": "simulated",
            "printer": "simulated",
            "paper_level": 100,
            "auth": "required" if token else "open",
        }

    @app.post("/device/printer/print")
    def print_job(body: PrintRequest, _: None = Depends(require_token)) -> dict[str, str]:
        SPOOL_DIR.mkdir(exist_ok=True)
        # Higiene del spool (regla 4, minimización de datos): el tótem atiende a
        # una persona a la vez y el trabajo anterior ya se "imprimió", así que no
        # se acumulan en disco justificantes de trabajos previos. Se conserva
        # solo el trabajo en curso; la purga de sesión limpia también este.
        for old in SPOOL_DIR.glob("*.txt"):
            old.unlink(missing_ok=True)
        job_id = f"job-{int(time.time())}-{secrets.token_hex(3)}"
        (SPOOL_DIR / f"{job_id}.txt").write_text("\n".join(body.lines), encoding="utf-8")
        return {"job_id": job_id, "status": "printed_simulated"}

    @app.post("/device/camera/capture")
    def capture(_: None = Depends(require_token)) -> dict[str, str]:
        encoded = base64.b64encode(_FAKE_CAPTURE_PNG).decode()
        return {"status": "simulated", "image_base64": encoded, "mime_type": "image/png"}

    @app.post("/device/session/purge")
    def purge_session(_: None = Depends(require_token)) -> dict[str, str]:
        """Borra cualquier resto local de la sesión (spool de impresión incluido)."""
        if SPOOL_DIR.exists():
            shutil.rmtree(SPOOL_DIR)
        return {"status": "purged"}

    return app


app = create_app()
