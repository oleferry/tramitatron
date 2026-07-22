"""Portal de pruebas local: un asistente de CITA PREVIA de varias páginas,
renderizado en el servidor (TT-502, demo reproducible).

Imita cómo funciona de verdad una cita previa de la administración: un asistente
por pasos —servicio → oficina → fecha/hora → datos— y, al final, un CAPTCHA y un
botón de confirmar. El worker debe recorrer los pasos, precompletar lo que puede
en cada página y DETENERSE ante el CAPTCHA, sin enviar nunca el formulario.

Los pasos intermedios navegan por GET (el 'Siguiente' del asistente); el envío
final es POST y responde 403 a propósito: si el worker intentara confirmar (lo
que NO debe hacer), el fallo sería visible y ruidoso.

Todo esto es un portal FICTICIO servido por el propio proyecto: no toca ninguna
administración real. Sirve para probar el flujo completo sin navegadores ni red.
"""

from fastapi import APIRouter, Response

router = APIRouter(prefix="/portal", tags=["portal-de-pruebas"])


def _page(body: str) -> Response:
    html = (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        "<title>Cita previa (portal de pruebas)</title></head><body>"
        f"{body}</body></html>"
    )
    return Response(content=html, media_type="text/html")


# Paso 1: elegir el servicio. 'Siguiente' navega por GET al paso de oficina.
@router.get("/cita")
def paso_servicio() -> Response:
    return _page(
        "<h1>Cita previa · paso 1 de 4: servicio</h1>"
        '<form method="get" action="/portal/cita/oficina">'
        '<label>Servicio <select name="servicio">'
        '<option value="">Elige…</option>'
        '<option value="renovacion-dni">Renovación del DNI</option>'
        '<option value="primera-inscripcion">Primera inscripción</option>'
        "</select></label>"
        '<button type="submit" name="siguiente">Siguiente</button>'
        "</form>"
    )


# Paso 2: elegir la oficina.
@router.get("/cita/oficina")
def paso_oficina() -> Response:
    return _page(
        "<h1>Cita previa · paso 2 de 4: oficina</h1>"
        '<form method="get" action="/portal/cita/fecha">'
        '<label>Oficina <select name="oficina">'
        '<option value="">Elige…</option>'
        '<option value="valladolid-centro">Valladolid — Centro</option>'
        '<option value="burgos-gamonal">Burgos — Gamonal</option>'
        "</select></label>"
        '<button type="submit" name="siguiente">Siguiente</button>'
        "</form>"
    )


# Paso 3: elegir fecha y hora.
@router.get("/cita/fecha")
def paso_fecha() -> Response:
    return _page(
        "<h1>Cita previa · paso 3 de 4: fecha y hora</h1>"
        '<form method="get" action="/portal/cita/datos">'
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


# Paso 4: datos de la persona + CAPTCHA + confirmar (muro de handoff). El envío
# es POST: el worker rellena nombre/DNI/teléfono y SE DETIENE aquí.
@router.get("/cita/datos")
def paso_datos() -> Response:
    return _page(
        "<h1>Cita previa · paso 4 de 4: tus datos</h1>"
        '<form method="post" action="/portal/cita/confirmar">'
        '<label>Nombre y apellidos <input type="text" name="nombre" value=""></label>'
        '<label>DNI <input type="text" name="dni" value=""></label>'
        '<label>Teléfono <input type="text" name="telefono" value=""></label>'
        '<div class="captcha"><label>Escribe el código de la imagen (captcha) '
        '<input type="text" name="captcha" value=""></label></div>'
        '<button type="submit" name="enviar">Confirmar cita</button>'
        "</form>"
    )


@router.post("/cita/confirmar")
def confirmar() -> Response:
    # El worker no debe llegar aquí jamás: la confirmación es de la persona.
    return Response(
        content="La confirmación de la cita corresponde a la persona, no al sistema.",
        media_type="text/plain",
        status_code=403,
    )
