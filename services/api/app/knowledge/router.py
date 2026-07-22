"""Asistente sobre contenido oficial (TT-303) y estado de las fuentes.

La respuesta es un EXTRACTO LITERAL del snapshot oficial, con organismo,
título, fecha de consulta y enlace (PRD §16.3). Si no hay contenido relevante,
se responde "no encontrado": nunca se rellena con conocimiento del modelo.
"""

from fastapi import APIRouter, Request

from .models import AskRequest, AskResponse, SourceInfo, SourceStatus
from .store import KnowledgeStore

router = APIRouter(prefix="/api", tags=["knowledge"])


@router.post("/assistant/ask")
def ask(body: AskRequest, request: Request) -> AskResponse:
    store: KnowledgeStore = request.app.state.knowledge
    # Uso del canal asistente (contador agregado; ni la pregunta ni la respuesta).
    request.app.state.metrics.record_channel("assistant")
    chunk = store.retrieve(body.text, procedure_id=body.procedure_id)
    if chunk is None:
        return AskResponse(found=False)

    source = store.sources[chunk.source_id]
    snapshot = store.snapshots[chunk.source_id]
    return AskResponse(
        found=True,
        answer=store.excerpt(chunk, body.text),
        source=SourceInfo(
            organismo=source.organismo,
            title=source.title,
            url=str(source.url),
            fetched_at=snapshot.fetched_at[:10],
        ),
    )


@router.get("/knowledge/sources")
def sources_status(request: Request) -> list[SourceStatus]:
    store: KnowledgeStore = request.app.state.knowledge
    result = []
    for source in store.sources.values():
        snapshot = store.snapshots.get(source.id)
        result.append(
            SourceStatus(
                id=source.id,
                organismo=source.organismo,
                title=source.title,
                url=str(source.url),
                review_cadence=source.review_cadence,
                snapshot_status=snapshot.status if snapshot else "pending",
                fetched_at=snapshot.fetched_at if snapshot else None,
            )
        )
    return result
