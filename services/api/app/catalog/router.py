"""Endpoints de catálogo de trámites (solo lectura; el catálogo es declarativo)."""

from fastapi import APIRouter, HTTPException, Request

from .models import CatalogSummaryItem, Procedure

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("")
def list_catalog(request: Request) -> list[CatalogSummaryItem]:
    catalog: dict[str, Procedure] = request.app.state.catalog
    return [
        CatalogSummaryItem(
            id=p.id,
            name=p.name,
            description=p.description,
            status=p.status,
            execution_mode=p.execution_mode,
        )
        for p in catalog.values()
        if p.status != "disabled"
    ]


@router.get("/{procedure_id}")
def get_procedure(procedure_id: str, request: Request) -> Procedure:
    catalog: dict[str, Procedure] = request.app.state.catalog
    procedure = catalog.get(procedure_id)
    if procedure is None or procedure.status == "disabled":
        raise HTTPException(status_code=404, detail="Trámite no encontrado")
    return procedure
