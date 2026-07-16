"""Endpoint del asistente: clasifica la intención del ciudadano.

El texto libre se procesa y se descarta: no se guarda ni se escribe en logs.
"""

from fastapi import APIRouter, Request

from .base import IntentRequest, IntentResult, ModelGateway

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/intent")
async def classify_intent(body: IntentRequest, request: Request) -> IntentResult:
    gateway: ModelGateway = request.app.state.gateway
    result = await gateway.classify_intent(body)
    # Si el gateway apunta a un trámite que no está en el catálogo, se deriva.
    if result.procedure_id and result.procedure_id not in request.app.state.catalog:
        return IntentResult(
            intent=result.intent,
            confidence=result.confidence,
            procedure_id=None,
            next_action="REFER_TO_HUMAN",
        )
    return result
