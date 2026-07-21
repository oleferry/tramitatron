"""Portal de pruebas local: un sitio de cita previa falso, renderizado en el
servidor (TT-502, demo reproducible).

Simula el trámite de una ITV: un formulario con matrícula y tipo de vehículo,
seguido de un CAPTCHA y un botón de envío. El worker debe rellenar los dos
primeros campos y DETENERSE ante el CAPTCHA, sin enviar nunca el formulario.
Sirve para probar el flujo de principio a fin sin tocar ningún portal real ni
descargar navegadores.

El POST responde 403 a propósito: si el worker intentara enviar el formulario
(lo que NO debe hacer), el fallo sería visible y ruidoso.
"""

from fastapi import APIRouter, Response

router = APIRouter(prefix="/portal", tags=["portal-de-pruebas"])

_FORM_HTML = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Cita ITV (portal de pruebas)</title></head>
<body>
  <h1>Reserva de cita para la ITV</h1>
  <form method="post" action="/portal/cita">
    <label>Matrícula <input type="text" name="matricula" value=""></label>
    <label>Tipo de vehículo
      <select name="tipo">
        <option value="">Elige…</option>
        <option value="coche">Coche</option>
        <option value="moto">Moto</option>
        <option value="furgoneta">Furgoneta</option>
      </select>
    </label>
    <div class="captcha">
      <label>Escribe el código de la imagen (captcha)
        <input type="text" name="captcha" value=""></label>
    </div>
    <button type="submit" name="enviar">Confirmar cita</button>
  </form>
</body></html>
"""


@router.get("/cita")
def cita_form() -> Response:
    return Response(content=_FORM_HTML, media_type="text/html")


@router.post("/cita")
def cita_submit() -> Response:
    # El worker no debe llegar aquí jamás: la confirmación es de la persona.
    return Response(
        content="La confirmación de la cita corresponde a la persona, no al sistema.",
        media_type="text/plain",
        status_code=403,
    )
