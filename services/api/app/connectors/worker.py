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
            )
        try:
            result = await self._post(
                "/worker/prepare",
                json={"connector": self._worker_connector, "fields": dict(data)},
            )
        except Exception:  # noqa: BLE001 - el tótem informa, no se rompe
            return ExecutionResult(
                status="failed",
                message="El asistente de navegación no está disponible ahora.",
            )

        if result.get("status") == "user_handoff":
            return ExecutionResult(
                status="user_handoff",
                receipt={
                    "url": result.get("url") or "",
                    "pending": ", ".join(result.get("pending", [])),
                },
            )
        # "unavailable" o "error": se traslada el mensaje del worker.
        return ExecutionResult(status="failed", message=result.get("message"))

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
