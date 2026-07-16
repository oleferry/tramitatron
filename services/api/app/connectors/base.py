"""Contrato del conector de trámites (PRD §12.3, simplificado para el hito 1).

Los conectores reales (GVA Salud, SITVAL) NO se implementan hasta que el núcleo
y las pruebas de privacidad estén completos. Solo existe el conector mock.
"""

from typing import Literal, Protocol

from pydantic import BaseModel


class ExecutionResult(BaseModel):
    status: Literal["completed", "failed", "user_handoff"]
    receipt: dict[str, str] | None = None
    message: str | None = None


class HealthcheckResult(BaseModel):
    connector: str
    healthy: bool
    detail: str | None = None


class TransactionConnector(Protocol):
    name: str

    async def execute(self, data: dict[str, str], confirmed: bool) -> ExecutionResult: ...

    async def healthcheck(self) -> HealthcheckResult: ...
