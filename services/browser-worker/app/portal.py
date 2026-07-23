"""Portal de pruebas local: un asistente de CITA CON EL MÉDICO de varias páginas,
renderizado en el servidor (TT-502, demo reproducible).

Réplica FIEL de cómo funciona de verdad la cita de atención primaria de Sacyl:
la identificación NO usa Cl@ve ni firma, solo el CIP (Código de Identificación
Personal, impreso en la tarjeta sanitaria) + el primer apellido. Luego se elige
centro y día/hora, y se confirma. Al ser una cita (reversible, anulable), el
sistema SÍ puede completarla, pero solo tras el "Sí, confirma" explícito del
ciudadano (que viaja como el flag de confirmación): sin ese flag, el envío se
rechaza. Un CAPTCHA, si lo hubiera, lo resuelve la persona.

Todo esto es un portal FICTICIO servido por el propio proyecto: no toca ninguna
administración real. Reproduce el flujo completo, incluida la confirmación, sin
navegadores ni red. El portal real (Sacyl) se conecta tras la EIPD (Fase 3).
"""

import secrets
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Response

router = APIRouter(prefix="/portal", tags=["portal-de-pruebas"])


def _page(body: str) -> Response:
    html = (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        "<title>Cita con el médico (portal de pruebas)</title></head><body>"
        f"{body}</body></html>"
    )
    return Response(content=html, media_type="text/html")


# Paso 1: identificación por tarjeta sanitaria (CIP + primer apellido). Sin
# Cl@ve. 'Siguiente' navega por GET al paso de centro.
@router.get("/cita")
def paso_identificacion() -> Response:
    return _page(
        "<h1>Cita con el médico · paso 1 de 4: identifícate</h1>"
        '<form method="get" action="/portal/cita/centro">'
        '<label>Código CIP de la tarjeta sanitaria '
        '<input type="text" name="cip" value=""></label>'
        '<label>Primer apellido <input type="text" name="apellido" value=""></label>'
        '<button type="submit" name="siguiente">Siguiente</button>'
        "</form>"
    )


# Paso 2: elegir el centro de salud.
@router.get("/cita/centro")
def paso_centro() -> Response:
    return _page(
        "<h1>Cita con el médico · paso 2 de 4: centro de salud</h1>"
        '<form method="get" action="/portal/cita/fecha">'
        '<label>Centro de salud <select name="centro">'
        '<option value="">Elige…</option>'
        '<option value="valladolid-pilarica">Valladolid — La Pilarica</option>'
        '<option value="burgos-gamonal">Burgos — Gamonal</option>'
        "</select></label>"
        '<button type="submit" name="siguiente">Siguiente</button>'
        "</form>"
    )


# Paso 3: elegir fecha y hora.
@router.get("/cita/fecha")
def paso_fecha() -> Response:
    return _page(
        "<h1>Cita con el médico · paso 3 de 4: fecha y hora</h1>"
        '<form method="get" action="/portal/cita/confirmar">'
        '<label>Fecha <select name="fecha">'
        '<option value="">Elige…</option>'
        '<option value="2026-09-01">1 de septiembre</option>'
        '<option value="2026-09-02">2 de septiembre</option>'
        "</select></label>"
        '<label>Hora <select name="hora">'
        '<option value="">Elige…</option>'
        '<option value="09:00">09:00</option>'
        '<option value="10:30">10:30</option>'
        "</select></label>"
        '<button type="submit" name="siguiente">Siguiente</button>'
        "</form>"
    )


# Paso 4: resumen y confirmación. El envío es POST. A diferencia de un trámite
# firmado, una cita se puede completar; pero SOLO con el flag de confirmación
# explícita del ciudadano (`confirmado=si`). Sin él, se rechaza: el sistema no
# reserva por su cuenta.
@router.get("/cita/confirmar")
def paso_confirmar() -> Response:
    return _page(
        "<h1>Cita con el médico · paso 4 de 4: confirma tu cita</h1>"
        '<form method="post" action="/portal/cita/confirmar">'
        '<input type="hidden" name="confirmado" value="si">'
        '<button type="submit" name="enviar">Confirmar cita</button>'
        "</form>"
    )


@router.post("/cita/confirmar")
async def confirmar(request: Request) -> Response:
    # Se lee el cuerpo urlencodificado a mano para no depender de python-multipart.
    form = parse_qs((await request.body()).decode())
    if form.get("confirmado", [""])[0] != "si":
        # Sin confirmación explícita, el sistema NO reserva.
        return Response(
            content="Falta la confirmación explícita del ciudadano.",
            media_type="text/plain",
            status_code=403,
        )
    referencia = f"CITA-{secrets.token_hex(3).upper()}"
    return _page(
        "<h1>Cita confirmada</h1>"
        f"<p>Tu cita está hecha. Referencia: <strong>{referencia}</strong></p>"
    )
