"""Endpoints de sesión efímera y anónima.

Reglas: el identificador es aleatorio, los valores de datos NUNCA se devuelven
en listados ni se escriben en logs, y el borrado (purga) es idempotente.
"""

import time
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from .store import Session, SessionStore

router = APIRouter(prefix="/api/session", tags=["session"])


class CreateSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: Literal["es", "ca-valencia"]


class SessionInfo(BaseModel):
    session_id: str
    language: str
    expires_in_seconds: float
    # Solo las CLAVES de los datos capturados; los valores no salen por este endpoint.
    data_keys: list[str]


class SetDataRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(pattern=r"^[a-z0-9_]{1,64}$")
    value: str = Field(min_length=1, max_length=2000)


def _store(request: Request) -> SessionStore:
    return request.app.state.store


def _info(session: Session) -> SessionInfo:
    return SessionInfo(
        session_id=session.id,
        language=session.language,
        expires_in_seconds=max(0.0, session.expires_at - time.monotonic()),
        data_keys=sorted(session.data.keys()),
    )


def _get_or_404(request: Request, session_id: str) -> Session:
    session = _store(request).get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sesión inexistente o expirada")
    return session


@router.post("", status_code=201)
def create_session(body: CreateSessionRequest, request: Request) -> SessionInfo:
    session = _store(request).create(body.language)
    # Métrica agregada: una sesión más, su idioma y su franja horaria. Sin el id.
    request.app.state.metrics.record_session(body.language)
    return _info(session)


@router.get("/{session_id}")
def get_session(session_id: str, request: Request) -> SessionInfo:
    return _info(_get_or_404(request, session_id))


@router.post("/{session_id}/extend")
def extend_session(session_id: str, request: Request) -> SessionInfo:
    session = _store(request).extend(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sesión inexistente o expirada")
    return _info(session)


@router.put("/{session_id}/data", status_code=204)
def set_session_data(session_id: str, body: SetDataRequest, request: Request) -> Response:
    if not _store(request).set_data(session_id, body.key, body.value):
        raise HTTPException(status_code=404, detail="Sesión inexistente o expirada")
    return Response(status_code=204)


@router.delete("/{session_id}", status_code=204)
def purge_session(session_id: str, request: Request) -> Response:
    # Idempotente: purgar una sesión ya purgada también devuelve 204.
    _store(request).purge(session_id)
    return Response(status_code=204)
