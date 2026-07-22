"""Panel institucional y KPIs (TT-602, PRD §18).

Dos tipos de endpoint:

- Ingesta (kiosco): señala hitos de uso NO personales (trámite iniciado o
  abandonado, satisfacción 1–5). Son públicos porque el kiosco es anónimo; el
  contenido es un contador, jamás datos de la persona.
- Lectura (operador): el cuadro de mando agregado, en JSON y CSV. Se protege
  con un token de administración si `ADMIN_TOKEN` está configurado (threat
  model D3). Sin token configurado, queda abierto para la demo local; como no
  contiene PII, el riesgo es de exposición de métricas, no de datos personales.
"""

import csv
import io

from fastapi import APIRouter, Header, HTTPException, Request, Response

from ..adminauth import require_admin as _require_admin
from ..catalog.models import Procedure
from .models import FeedbackRequest, ProcedureEventRequest
from .registry import MetricsRegistry

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


def _registry(request: Request) -> MetricsRegistry:
    return request.app.state.metrics


@router.post("/event", status_code=204)
def record_event(body: ProcedureEventRequest, request: Request) -> Response:
    catalog: dict[str, Procedure] = request.app.state.catalog
    # Solo trámites reales del catálogo: nada de ids inventados que ensucien el panel.
    if body.procedure_id not in catalog:
        raise HTTPException(status_code=404, detail="Trámite no encontrado")
    _registry(request).record_procedure(body.procedure_id, body.type)
    return Response(status_code=204)


@router.post("/feedback", status_code=204)
def record_feedback(body: FeedbackRequest, request: Request) -> Response:
    catalog: dict[str, Procedure] = request.app.state.catalog
    if body.procedure_id is not None and body.procedure_id not in catalog:
        raise HTTPException(status_code=404, detail="Trámite no encontrado")
    _registry(request).record_satisfaction(body.rating)
    return Response(status_code=204)


@router.get("/summary")
def summary(request: Request, authorization: str | None = Header(default=None)) -> dict:
    _require_admin(request, authorization)
    return _registry(request).snapshot()


@router.get("/summary.csv")
def summary_csv(request: Request, authorization: str | None = Header(default=None)) -> Response:
    _require_admin(request, authorization)
    snap = _registry(request).snapshot()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["seccion", "clave", "valor"])
    writer.writerow(["meta", "desde", snap["since"]])
    writer.writerow(["meta", "generado", snap["generated_at"]])

    usage = snap["usage"]
    writer.writerow(["uso", "sesiones", usage["sessions"]])
    for lang, n in sorted(usage["by_language"].items()):
        writer.writerow(["uso_idioma", lang, n])
    for hour, n in sorted(usage["by_hour"].items()):
        writer.writerow(["uso_franja", f"{hour:02d}h", n])
    for channel, n in sorted(usage["channels"].items()):
        writer.writerow(["uso_canal", channel, n])

    proc = snap["procedures"]
    for key, value in proc["totals"].items():
        writer.writerow(["tramites_total", key, value])
    writer.writerow(["tramites_kpi", "tasa_exito_pct", proc["success_rate_pct"]])
    writer.writerow(["tramites_kpi", "tasa_derivacion_pct", proc["handoff_rate_pct"]])
    writer.writerow(["tramites_kpi", "tasa_abandono_pct", proc["abandonment_rate_pct"]])
    for pid, counters in sorted(proc["by_procedure"].items()):
        for ev, value in counters.items():
            writer.writerow(["tramite", f"{pid}:{ev}", value])

    sat = snap["satisfaction"]
    writer.writerow(["satisfaccion", "votos", sat["votes"]])
    writer.writerow(["satisfaccion", "media", sat["average"]])
    for rating, n in sorted(sat["histogram"].items()):
        writer.writerow(["satisfaccion_histograma", f"{rating}", n])

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=tramitatron-kpis.csv"},
    )
