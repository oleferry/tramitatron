"""Portales de pruebas locales: dos asistentes de CITA PREVIA de varias páginas,
renderizados en el servidor (TT-502, demo reproducible).

Réplicas FIELES de los dos trámites objetivo, que comparten lo esencial: la
identificación NO usa Cl@ve, certificado ni firma, sino datos que el ciudadano
lleva encima, y la cita es reversible (se puede anular). Por eso el sistema SÍ
puede completarlas, pero solo tras el "Sí, confirma" explícito del ciudadano
(que viaja como el flag de confirmación); sin él, el envío se rechaza.

- Cita con el médico (Sacyl): CIP de la tarjeta sanitaria + primer apellido.
- Cita en Hacienda (AEAT):    NIF + nombre y apellidos.

Todo esto es FICTICIO y lo sirve el propio proyecto: no toca ninguna
administración real. Reproduce el flujo completo, incluida la confirmación, sin
navegadores ni red. Los portales reales se conectan tras la EIPD.
"""

import secrets
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Response

router = APIRouter(prefix="/portal", tags=["portal-de-pruebas"])


def _page(body: str) -> Response:
    html = (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        "<title>Cita previa (portal de pruebas)</title></head><body>"
        f"{body}</body></html>"
    )
    return Response(content=html, media_type="text/html")


async def _confirmar(request: Request, prefijo: str) -> Response:
    """Confirmación final compartida. Se lee el cuerpo urlencodificado a mano
    para no depender de python-multipart."""
    form = parse_qs((await request.body()).decode())
    if form.get("confirmado", [""])[0] != "si":
        # Sin confirmación explícita, el sistema NO reserva.
        return Response(
            content="Falta la confirmación explícita del ciudadano.",
            media_type="text/plain",
            status_code=403,
        )
    referencia = f"{prefijo}-{secrets.token_hex(3).upper()}"
    return _page(
        "<h1>Cita confirmada</h1>"
        f"<p>Tu cita está hecha. Referencia: <strong>{referencia}</strong></p>"
    )


# ── Cita con el médico (réplica de Sacyl) ──────────────────────────────────
# Identificación por CIP + primer apellido, sin Cl@ve: así funciona de verdad.


@router.get("/cita")
def salud_identificacion() -> Response:
    return _page(
        "<h1>Cita con el médico · paso 1 de 4: identifícate</h1>"
        '<form method="get" action="/portal/cita/centro">'
        '<label>Código CIP de la tarjeta sanitaria '
        '<input type="text" name="cip" value=""></label>'
        '<label>Primer apellido <input type="text" name="apellido" value=""></label>'
        '<button type="submit" name="siguiente">Siguiente</button>'
        "</form>"
    )


@router.get("/cita/centro")
def salud_centro() -> Response:
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


@router.get("/cita/fecha")
def salud_fecha() -> Response:
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


@router.get("/cita/confirmar")
def salud_confirmar_pagina() -> Response:
    return _page(
        "<h1>Cita con el médico · paso 4 de 4: confirma tu cita</h1>"
        '<form method="post" action="/portal/cita/confirmar">'
        '<input type="hidden" name="confirmado" value="si">'
        '<button type="submit" name="enviar">Confirmar cita</button>'
        "</form>"
    )


@router.post("/cita/confirmar")
async def salud_confirmar(request: Request) -> Response:
    return await _confirmar(request, "CITA")


# ── Cita en Hacienda (réplica de AEAT) ─────────────────────────────────────
# La propia AEAT indica que para pedir cita NO hace falta certificado, DNIe ni
# Cl@ve: basta con NIF y nombre y apellidos.


@router.get("/hacienda/cita")
def aeat_identificacion() -> Response:
    return _page(
        "<h1>Cita en Hacienda · paso 1 de 4: identifícate</h1>"
        '<form method="get" action="/portal/hacienda/cita/gestion">'
        '<label>NIF <input type="text" name="nif" value=""></label>'
        '<label>Nombre y apellidos <input type="text" name="nombre" value=""></label>'
        '<button type="submit" name="siguiente">Siguiente</button>'
        "</form>"
    )


@router.get("/hacienda/cita/gestion")
def aeat_gestion() -> Response:
    return _page(
        "<h1>Cita en Hacienda · paso 2 de 4: qué gestión</h1>"
        '<form method="get" action="/portal/hacienda/cita/fecha">'
        '<label>Gestión <select name="gestion">'
        '<option value="">Elige…</option>'
        '<option value="informacion-renta">Información sobre la Renta</option>'
        '<option value="certificados">Certificados tributarios</option>'
        '<option value="censo">Alta o cambio de datos censales</option>'
        "</select></label>"
        '<button type="submit" name="siguiente">Siguiente</button>'
        "</form>"
    )


@router.get("/hacienda/cita/fecha")
def aeat_fecha() -> Response:
    return _page(
        "<h1>Cita en Hacienda · paso 3 de 4: oficina, fecha y hora</h1>"
        '<form method="get" action="/portal/hacienda/cita/confirmar">'
        '<label>Oficina <select name="oficina">'
        '<option value="">Elige…</option>'
        '<option value="valladolid">Valladolid</option>'
        '<option value="burgos">Burgos</option>'
        "</select></label>"
        '<label>Fecha <select name="fecha">'
        '<option value="">Elige…</option>'
        '<option value="2026-09-03">3 de septiembre</option>'
        '<option value="2026-09-04">4 de septiembre</option>'
        "</select></label>"
        '<label>Hora <select name="hora">'
        '<option value="">Elige…</option>'
        '<option value="09:30">09:30</option>'
        '<option value="11:00">11:00</option>'
        "</select></label>"
        '<button type="submit" name="siguiente">Siguiente</button>'
        "</form>"
    )


@router.get("/hacienda/cita/confirmar")
def aeat_confirmar_pagina() -> Response:
    return _page(
        "<h1>Cita en Hacienda · paso 4 de 4: confirma tu cita</h1>"
        '<form method="post" action="/portal/hacienda/cita/confirmar">'
        '<input type="hidden" name="confirmado" value="si">'
        '<button type="submit" name="enviar">Confirmar cita</button>'
        "</form>"
    )


@router.post("/hacienda/cita/confirmar")
async def aeat_confirmar(request: Request) -> Response:
    return await _confirmar(request, "AEAT")


# ── Cita en la Seguridad Social (réplica del INSS) ─────────────────────────
# La sede del INSS permite pedir cita "sin certificado": basta con nombre y
# apellidos, DNI/NIE y un teléfono móvil. El teléfono NO está en el DNI, así que
# es el único dato que la persona teclea.


@router.get("/inss/cita")
def inss_identificacion() -> Response:
    return _page(
        "<h1>Cita en la Seguridad Social · paso 1 de 4: identifícate</h1>"
        '<form method="get" action="/portal/inss/cita/prestacion">'
        '<label>DNI o NIE <input type="text" name="nif" value=""></label>'
        '<label>Nombre y apellidos <input type="text" name="nombre" value=""></label>'
        '<label>Teléfono móvil <input type="text" name="telefono" value=""></label>'
        '<button type="submit" name="siguiente">Siguiente</button>'
        "</form>"
    )


@router.get("/inss/cita/prestacion")
def inss_prestacion() -> Response:
    return _page(
        "<h1>Cita en la Seguridad Social · paso 2 de 4: qué necesitas</h1>"
        '<form method="get" action="/portal/inss/cita/fecha">'
        '<label>Prestación <select name="prestacion">'
        '<option value="">Elige…</option>'
        '<option value="jubilacion">Jubilación</option>'
        '<option value="incapacidad">Incapacidad permanente</option>'
        '<option value="viudedad">Viudedad y otras prestaciones</option>'
        "</select></label>"
        '<button type="submit" name="siguiente">Siguiente</button>'
        "</form>"
    )


@router.get("/inss/cita/fecha")
def inss_fecha() -> Response:
    return _page(
        "<h1>Cita en la Seguridad Social · paso 3 de 4: oficina, fecha y hora</h1>"
        '<form method="get" action="/portal/inss/cita/confirmar">'
        '<label>Oficina <select name="oficina">'
        '<option value="">Elige…</option>'
        '<option value="valladolid">Valladolid</option>'
        '<option value="burgos">Burgos</option>'
        "</select></label>"
        '<label>Fecha <select name="fecha">'
        '<option value="">Elige…</option>'
        '<option value="2026-09-08">8 de septiembre</option>'
        '<option value="2026-09-09">9 de septiembre</option>'
        "</select></label>"
        '<label>Hora <select name="hora">'
        '<option value="">Elige…</option>'
        '<option value="10:00">10:00</option>'
        '<option value="12:00">12:00</option>'
        "</select></label>"
        '<button type="submit" name="siguiente">Siguiente</button>'
        "</form>"
    )


@router.get("/inss/cita/confirmar")
def inss_confirmar_pagina() -> Response:
    return _page(
        "<h1>Cita en la Seguridad Social · paso 4 de 4: confirma tu cita</h1>"
        '<form method="post" action="/portal/inss/cita/confirmar">'
        '<input type="hidden" name="confirmado" value="si">'
        '<button type="submit" name="enviar">Confirmar cita</button>'
        "</form>"
    )


@router.post("/inss/cita/confirmar")
async def inss_confirmar(request: Request) -> Response:
    return await _confirmar(request, "INSS")
