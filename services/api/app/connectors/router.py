"""Ejecución de trámites vía conector y estado de salud de conectores.

En el hito 1 solo puede ejecutarse el conector mock. Cualquier trámite con
conector real devuelve 501 hasta que exista implementación probada.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from ..catalog.models import Procedure
from .base import ExecutionResult, HealthcheckResult, TransactionConnector

router = APIRouter(prefix="/api", tags=["connectors"])


class ExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    confirmed: bool = False


@router.get("/connectors/health")
async def connectors_health(request: Request) -> list[HealthcheckResult]:
    connectors: dict[str, TransactionConnector] = request.app.state.connectors
    return [await c.healthcheck() for c in connectors.values()]


@router.post("/procedures/{procedure_id}/execute")
async def execute_procedure(
    procedure_id: str, body: ExecuteRequest, request: Request
) -> ExecutionResult:
    catalog: dict[str, Procedure] = request.app.state.catalog
    procedure = catalog.get(procedure_id)
    if procedure is None:
        raise HTTPException(status_code=404, detail="Trámite no encontrado")

    session = request.app.state.store.get(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sesión inexistente o expirada")

    if procedure.status != "available":
        raise HTTPException(status_code=409, detail="Trámite no disponible actualmente")

    connector = request.app.state.connectors.get(procedure.connector.package)
    if connector is None:
        raise HTTPException(status_code=501, detail="Conector no implementado")

    if procedure.confirmation_required and not body.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Este trámite requiere confirmación explícita del usuario",
        )

    # Los datos de la sesión se pasan al conector y viven solo durante la llamada.
    result = await connector.execute(dict(session.data), confirmed=body.confirmed)

    # Métrica agregada del desenlace (PRD §18.1 Eficiencia): éxito, derivación o
    # fallo por trámite. Solo cuenta el estado; ningún dato de la persona.
    _EVENT_BY_STATUS = {
        "completed": "completed",
        "user_handoff": "handoff",
        "failed": "failed",
    }
    event = _EVENT_BY_STATUS.get(result.status)
    if event:
        request.app.state.metrics.record_procedure(procedure_id, event)

    return result
