"""Registro de tótems y salud del parque (TT-601, PRD §9.2 «estado de dispositivos»).

- Latido (tótem → API): ingesta del estado del dispositivo. Puede protegerse
  con `TOTEM_TOKEN` (cabecera `X-Totem-Token`), igual que el device-agent; sin
  token, queda abierto para la demo local. Da de alta al tótem si no estaba
  declarado.
- Lectura (operador): parque + salud, agregado. Protegido con `ADMIN_TOKEN` si
  está configurado (mismo criterio que el panel de KPIs).
"""

import secrets

from fastapi import APIRouter, Header, HTTPException, Path, Request, Response

from ..adminauth import require_admin
from .models import TOTEM_ID_PATTERN, FleetView, HeartbeatRequest, TotemStatus
from .registry import TotemRegistry

router = APIRouter(prefix="/api/totems", tags=["totems"])

_TotemId = Path(pattern=TOTEM_ID_PATTERN)


def _registry(request: Request) -> TotemRegistry:
    return request.app.state.totems


def _check_totem_token(request: Request, token_header: str | None) -> None:
    token = request.app.state.settings.totem_token
    if not token:
        return
    if token_header is None or not secrets.compare_digest(token_header, token):
        raise HTTPException(status_code=401, detail="Latido no autorizado")


@router.post("/{totem_id}/heartbeat", status_code=204)
def heartbeat(
    body: HeartbeatRequest,
    request: Request,
    totem_id: str = _TotemId,
    x_totem_token: str | None = Header(default=None),
) -> Response:
    _check_totem_token(request, x_totem_token)
    _registry(request).heartbeat(totem_id, body.version, body.peripherals)
    return Response(status_code=204)


@router.get("")
def fleet(request: Request, authorization: str | None = Header(default=None)) -> FleetView:
    require_admin(request, authorization)
    return _registry(request).snapshot()


@router.get("/{totem_id}")
def totem(
    request: Request,
    totem_id: str = _TotemId,
    authorization: str | None = Header(default=None),
) -> TotemStatus:
    require_admin(request, authorization)
    status = _registry(request).get(totem_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Tótem no encontrado")
    return status
