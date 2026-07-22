"""Protección de la lectura del panel institucional (TT-602/TT-601).

Si `ADMIN_TOKEN` está configurado, los endpoints de solo lectura del panel
(KPIs y salud de tótems) exigen `Authorization: Bearer <token>` (threat model
D3). Sin token configurado, quedan abiertos para la demo local; no contienen
PII, solo agregados y datos operativos del dispositivo.

La INGESTA (métricas del kiosco, latidos de tótem) no pasa por aquí: tiene su
propia política, más laxa, porque procede de dispositivos anónimos/confiables.
"""

import secrets

from fastapi import HTTPException, Request


def require_admin(request: Request, authorization: str | None) -> None:
    token = request.app.state.settings.admin_token
    if not token:
        return
    expected = f"Bearer {token}"
    # Comparación en tiempo constante: no filtrar el token por timing.
    if authorization is None or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Panel restringido")
