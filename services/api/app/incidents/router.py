"""Incidencias y soporte (TT-603, PRD §13.3/§19).

- Alta (kiosco/dispositivo): reporta una degradación (backend caído, impresora,
  conector…) y RECIBE el código anónimo para enseñárselo al ciudadano (PRD §5,
  «código de incidencia anónimo»). Pública como el resto de la ingesta del
  kiosco; el error se redacta al guardar.
- Lectura y resolución (operador): lista, detalle y cierre. Protegidas con
  `ADMIN_TOKEN` como el resto del panel.
"""

from fastapi import APIRouter, Header, HTTPException, Request

from ..adminauth import require_admin
from .models import (
    Incident,
    IncidentReport,
    IncidentStatus,
    IncidentSummary,
    ResolveRequest,
    Severity,
)
from .registry import IncidentRegistry

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


def _registry(request: Request) -> IncidentRegistry:
    return request.app.state.incidents


@router.post("", status_code=201)
def report_incident(body: IncidentReport, request: Request) -> Incident:
    return _registry(request).open_from_report(body)


@router.get("")
def list_incidents(
    request: Request,
    status: IncidentStatus | None = None,
    severity: Severity | None = None,
    component: str | None = None,
    authorization: str | None = Header(default=None),
) -> dict:
    require_admin(request, authorization)
    reg = _registry(request)
    return {
        "summary": reg.summary().model_dump(),
        "incidents": [i.model_dump() for i in reg.list(status, severity, component)],
    }


@router.get("/summary")
def incidents_summary(
    request: Request, authorization: str | None = Header(default=None)
) -> IncidentSummary:
    require_admin(request, authorization)
    return _registry(request).summary()


@router.get("/{code}")
def get_incident(
    code: str, request: Request, authorization: str | None = Header(default=None)
) -> Incident:
    require_admin(request, authorization)
    incident = _registry(request).get(code)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return incident


@router.post("/{code}/resolve")
def resolve_incident(
    code: str,
    body: ResolveRequest,
    request: Request,
    authorization: str | None = Header(default=None),
) -> Incident:
    require_admin(request, authorization)
    incident = _registry(request).resolve(code, body.note)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return incident
