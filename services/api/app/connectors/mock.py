"""Conector mock: simula un trámite completo sin tocar ningún portal externo.

Demuestra el contrato: nunca ejecuta sin confirmación explícita del usuario y
devuelve un justificante sin datos personales.
"""

import secrets
from datetime import UTC, datetime

from .base import ExecutionResult, HealthcheckResult


class MockConnector:
    name = "demo.mock"

    async def execute(self, data: dict[str, str], confirmed: bool) -> ExecutionResult:
        if not confirmed:
            return ExecutionResult(
                status="failed",
                message="El trámite requiere confirmación explícita del usuario.",
            )
        return ExecutionResult(
            status="completed",
            receipt={
                "reference": f"DEMO-{secrets.token_hex(4).upper()}",
                "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                "kind": "demo",
            },
        )

    async def healthcheck(self) -> HealthcheckResult:
        return HealthcheckResult(connector=self.name, healthy=True, detail="simulado")
