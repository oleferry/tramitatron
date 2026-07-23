"""Conector que delega en el worker de navegación asistida (servicio separado).

Traduce el resultado del worker (`prepare`) al contrato de conector de la API.
El worker prepara y cede, así que este conector NUNCA devuelve "completed":
el único desenlace bueno es `user_handoff`, con la URL oficial y lo que la
persona debe hacer a mano (CAPTCHA, identificación, confirmación).

Sin worker configurado o accesible, devuelve "failed" con un mensaje claro:
un tótem sin worker no debe romperse, solo informar de que no está disponible.
"""

import httpx

from .base import ExecutionResult, HealthcheckResult


class WorkerConnector:
    def __init__(
        self,
        *,
        name: str,
        worker_url: str | None,
        worker_connector: str,
        client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.name = name
        self._worker_url = worker_url.rstrip("/") if worker_url else None
        self._worker_connector = worker_connector
        self._client = client
        self._timeout = timeout_seconds

    async def _post(self, path: str, json: dict | None = None) -> dict:
        if self._client is not None:
            response = await self._client.post(path, json=json, timeout=self._timeout)
        else:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(f"{self._worker_url}{path}", json=json)
        response.raise_for_status()
        return response.json()

    async def execute(self, data: dict[str, str], confirmed: bool) -> ExecutionResult:
        if not confirmed:
            return ExecutionResult(
                status="failed",
                message="El trámite requiere confirmación explícita del usuario.",
            )
        if self._worker_url is None and self._client is None:
            return ExecutionResult(
                status="failed",
                message="El asistente de navegación no está disponible ahora.",
                technical_detail="worker no configurado (BROWSER_WORKER_URL)",
            )
        # El mensaje al ciudadano es siempre el mismo; el detalle técnico (para
        # la incidencia de soporte) distingue la causa. Nunca lleva datos de la
        # persona: solo el tipo de error o el código HTTP.
        _UNAVAILABLE = "El asistente de navegación no está disponible ahora."
        try:
            result = await self._post(
                "/worker/prepare",
                json={
                    "connector": self._worker_connector,
                    "fields": dict(data),
                    # La confirmación del ciudadano se traslada al worker: solo
                    # con ella (y si el trámite es completable) se envía la cita.
                    "confirm": confirmed,
                },
            )
        except httpx.HTTPStatusError as exc:
            return ExecutionResult(
                status="failed",
                message=_UNAVAILABLE,
                technical_detail=f"worker respondió HTTP {exc.response.status_code}",
            )
        except httpx.HTTPError as exc:
            # Timeout, conexión rechazada, DNS… el nombre de la clase basta para
            # el diagnóstico y no contiene datos de la petición.
            return ExecutionResult(
                status="failed",
                message=_UNAVAILABLE,
                technical_detail=f"worker inaccesible: {type(exc).__name__}",
            )
        except Exception as exc:  # noqa: BLE001 - el tótem informa, no se rompe
            return ExecutionResult(
                status="failed",
                message=_UNAVAILABLE,
                technical_detail=f"error inesperado: {type(exc).__name__}",
            )

        if result.get("status") == "completed":
            # Cita reservada tras la confirmación del ciudadano: justificante con
            # la referencia, como cualquier trámite completado.
            return ExecutionResult(
                status="completed",
                receipt={
                    "reference": result.get("reference") or "",
                    "url": result.get("url") or "",
                },
            )
        if result.get("status") == "user_handoff":
            return ExecutionResult(
                status="user_handoff",
                receipt={
                    "url": result.get("url") or "",
                    "pending": ", ".join(result.get("pending", [])),
                },
            )
        # "unavailable" o "error": el mensaje del worker va al ciudadano y el
        # estado sirve de rastro técnico para soporte.
        return ExecutionResult(
            status="failed",
            message=result.get("message"),
            technical_detail=f"worker status={result.get('status')}",
        )

    async def healthcheck(self) -> HealthcheckResult:
        if self._worker_url is None and self._client is None:
            return HealthcheckResult(connector=self.name, healthy=False, detail="no configurado")
        try:
            result = await self._post(f"/worker/healthcheck/{self._worker_connector}")
        except Exception:  # noqa: BLE001
            return HealthcheckResult(connector=self.name, healthy=False, detail="inaccesible")
        return HealthcheckResult(
            connector=self.name,
            healthy=bool(result.get("healthy")),
            detail=result.get("detail"),
        )
