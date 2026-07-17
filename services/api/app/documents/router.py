"""Servicio documental efímero (PRD §11).

Pipeline: CAPTURE (kiosco/device-agent) → QUALITY_CHECK → EXTRACT (gateway)
→ VALIDATE (deterministas) → USER_CONFIRM → USE_IN_SESSION → PURGE.

La extracción se guarda como JSON dentro de los datos de la sesión, de modo
que hereda su TTL y su purga: no existe ningún otro almacén de documentos.
La imagen solo vive durante la petición; nunca se escribe en disco ni en logs.
"""

import base64
import binascii
import json
import uuid

from fastapi import APIRouter, HTTPException, Request, Response

from ..gateway.base import DocumentRequest, ModelGateway
from ..sessions.store import Session, SessionStore
from .models import (
    MAX_IMAGE_BYTES,
    REVIEW_CONFIDENCE_THRESHOLD,
    ConfirmDocumentRequest,
    ConfirmDocumentResponse,
    DocumentExtraction,
    ExtractedField,
    UploadDocumentRequest,
)
from .validators import validator_for

router = APIRouter(prefix="/api/session/{session_id}/documents", tags=["documents"])

_DOC_KEY_PREFIX = "document_"


def _store(request: Request) -> SessionStore:
    return request.app.state.store


def _get_session_or_404(request: Request, session_id: str) -> Session:
    session = _store(request).get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sesión inexistente o expirada")
    return session


def _quality_check(image_base64: str) -> None:
    try:
        decoded = base64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Imagen ilegible (base64 inválido)") from exc
    if not decoded:
        raise HTTPException(status_code=400, detail="Imagen vacía")
    if len(decoded) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Imagen demasiado grande")


def _validate_field(field: str, value: str, confidence: float) -> ExtractedField:
    validator_id, check = validator_for(field)
    if not check(value):
        status = "INVALID"
    elif confidence < REVIEW_CONFIDENCE_THRESHOLD:
        status = "REVIEW_REQUIRED"
    else:
        status = "VALID"
    return ExtractedField(
        field=field, value=value, confidence=confidence, validator=validator_id, status=status
    )


@router.post("", status_code=201)
async def upload_document(
    session_id: str, body: UploadDocumentRequest, request: Request
) -> DocumentExtraction:
    _get_session_or_404(request, session_id)
    _quality_check(body.image_base64)

    gateway: ModelGateway = request.app.state.gateway
    result = await gateway.extract_document(
        DocumentRequest(
            document_class=body.document_class,
            image_base64=body.image_base64,
            mime_type=body.mime_type,
        )
    )

    extraction = DocumentExtraction(
        document_id=uuid.uuid4().hex[:12],
        document_class=body.document_class,
        fields=[_validate_field(f.field, f.value, f.confidence) for f in result.fields],
    )

    # La extracción vive dentro de la sesión: mismo TTL, misma purga.
    _store(request).set_data(
        session_id,
        _DOC_KEY_PREFIX + extraction.document_id,
        extraction.model_dump_json(),
    )
    return extraction


@router.post("/{document_id}/confirm")
def confirm_document(
    session_id: str, document_id: str, body: ConfirmDocumentRequest, request: Request
) -> ConfirmDocumentResponse:
    session = _get_session_or_404(request, session_id)
    doc_key = _DOC_KEY_PREFIX + document_id
    raw = session.data.get(doc_key)
    if raw is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado en la sesión")

    extraction = DocumentExtraction.model_validate(json.loads(raw))
    known_fields = {f.field for f in extraction.fields}
    unknown = set(body.fields) - known_fields
    if unknown:
        raise HTTPException(
            status_code=422, detail=f"Campos ajenos al documento: {sorted(unknown)}"
        )

    # El ciudadano ha revisado los valores: la confianza pasa a 1.0 y solo
    # cuentan los validadores deterministas.
    results = [_validate_field(field, value, 1.0) for field, value in body.fields.items()]
    accepted = all(f.status == "VALID" for f in results)

    if accepted:
        store = _store(request)
        for f in results:
            store.set_data(session_id, f.field, f.value)
        # La extracción cruda ya no es necesaria: se elimina.
        store.remove_data(session_id, doc_key)

    return ConfirmDocumentResponse(accepted=accepted, fields=results)


@router.delete("/{document_id}", status_code=204)
def purge_document(session_id: str, document_id: str, request: Request) -> Response:
    _get_session_or_404(request, session_id)
    _store(request).remove_data(session_id, _DOC_KEY_PREFIX + document_id)
    return Response(status_code=204)
