"""Agente local de periféricos del tótem — MODO SIMULADOR (TT-401).

En el hito 1 no hay hardware: la impresora escribe ficheros de texto en un
directorio de spool local y la cámara devuelve una imagen sintética fija.
El agente solo debe escuchar en localhost (PRD §17.2); nunca se expone a red.
"""

import base64
import secrets
import shutil
import time
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

SPOOL_DIR = Path(__file__).resolve().parents[1] / "spool"

# PNG gris de 1x1 px: sustituto sintético de una captura de cámara.
_FAKE_CAPTURE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNiAAAABgADNjd8qAAAAABJRU5ErkJggg=="
)

app = FastAPI(title="Tramitatrón Device Agent (simulador)", version="0.1.0")


class PrintRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lines: list[str] = Field(min_length=1, max_length=40)


@app.get("/device/health")
def health() -> dict:
    return {
        "status": "ok",
        "mode": "simulator",
        "camera": "simulated",
        "scanner": "simulated",
        "printer": "simulated",
        "paper_level": 100,
    }


@app.post("/device/printer/print")
def print_job(body: PrintRequest) -> dict[str, str]:
    SPOOL_DIR.mkdir(exist_ok=True)
    job_id = f"job-{int(time.time())}-{secrets.token_hex(3)}"
    (SPOOL_DIR / f"{job_id}.txt").write_text("\n".join(body.lines), encoding="utf-8")
    return {"job_id": job_id, "status": "printed_simulated"}


@app.post("/device/camera/capture")
def capture() -> dict[str, str]:
    encoded = base64.b64encode(_FAKE_CAPTURE_PNG).decode()
    return {"status": "simulated", "image_base64": encoded, "mime_type": "image/png"}


@app.post("/device/session/purge")
def purge_session() -> dict[str, str]:
    """Borra cualquier resto local de la sesión (spool de impresión incluido)."""
    if SPOOL_DIR.exists():
        shutil.rmtree(SPOOL_DIR)
    return {"status": "purged"}
