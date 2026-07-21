"""Límite de peticiones por cliente (ENS mp.s.2, threat model D4).

Ventana fija en memoria: cuenta las peticiones de cada cliente en una ventana de
tiempo y responde 429 al superar el límite. El estado vive en la instancia de la
app (no es global), así que cada proceso tiene el suyo.

Limitación conocida: con varios workers/instancias, el límite es por proceso. Un
despliegue con varias réplicas debería llevar el contador a Redis; para el
micro-piloto (un tótem, una instancia) la ventana en memoria es suficiente.

El identificador del cliente respeta el proxy (X-Forwarded-For), sin registrar
la IP en ningún log (solo se usa como clave en memoria).
"""

import time


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # clave -> (inicio_de_ventana, contador)
        self._windows: dict[str, tuple[float, int]] = {}

    @property
    def enabled(self) -> bool:
        return self.max_requests > 0

    def check(self, key: str, now: float | None = None) -> tuple[bool, float]:
        """Devuelve (permitido, segundos_para_reintentar).

        Cuando se supera el límite, el segundo valor es el tiempo que falta para
        que la ventana se reinicie (para la cabecera Retry-After).
        """
        if not self.enabled:
            return True, 0.0
        now = time.monotonic() if now is None else now
        start, count = self._windows.get(key, (now, 0))
        if now - start >= self.window_seconds:
            # Ventana caducada: empieza una nueva.
            self._windows[key] = (now, 1)
            return True, 0.0
        if count >= self.max_requests:
            return False, self.window_seconds - (now - start)
        self._windows[key] = (start, count + 1)
        return True, 0.0


def client_key(request) -> str:
    """Clave del cliente: primer salto de X-Forwarded-For, o la IP directa."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"
